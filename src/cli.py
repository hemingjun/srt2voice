import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from .config import ConfigManager
from .parser.srt import SRTParser
from .utils.logger import setup_logger
from .utils.session import create_session, get_current_session
from .tts import TTS_SERVICES
from .audio import AudioProcessor
from .audio.exceptions import AudioTooLongError
from .audio.processor import ProcessingStatistics
from .cache.manager import init_cache
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

console = Console()


@click.command()
@click.argument('input_file', nargs=-1, required=False)
@click.option('-o', '--output', 'output_file',
              help='Output audio file path (default: same as input with .wav extension)')
@click.option('-c', '--config', 'config_path', 
              default='config/default.yaml',
              help='Configuration file path')
@click.option('-s', '--service', 'service_name',
              help='TTS service to use')
@click.option('--preview', type=int, 
              help='Preview mode: process only first N subtitles')
@click.option('--debug', is_flag=True, 
              help='Enable debug mode with verbose logging')
@click.option('--list-services', is_flag=True,
              help='List available TTS services and exit')
@click.version_option(version='0.1.0', prog_name='srt2speech')
def main(input_file, output_file, config_path, service_name, preview, debug, list_services):
    """Convert SRT subtitle files to speech audio using TTS services.
    
    Example:
        srt2speech input.srt
        srt2speech input.srt --service gemini
        srt2speech input.srt --preview 5
        srt2speech --list-services
    """
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        
        # Setup logging
        log_level = 'DEBUG' if debug else config_manager.config.logging['level']
        logger = setup_logger('srt2speech', log_level)
        
        # Create session for consistent voice generation
        session = create_session()
        
        # Initialize cache
        cache_manager = init_cache(config_manager.config.cache)
        
        # List services and exit if requested
        if list_services:
            list_available_services(config_manager)
            return
        
        # Process input file argument(s)
        if not input_file:
            console.print("[red]Error:[/red] Input SRT file is required.")
            console.print("Usage: srt2speech <srt_file>")
            sys.exit(1)
        
        # Handle multiple arguments (path with spaces)
        if len(input_file) > 1:
            # Try to join arguments with space
            potential_path = ' '.join(input_file)
            if Path(potential_path).exists():
                input_file = potential_path
                logger.debug(f"Joined multiple arguments into path: {input_file}")
            else:
                # If joined path doesn't exist, try the first argument only
                if Path(input_file[0]).exists():
                    input_file = input_file[0]
                    if len(input_file) > 1:
                        console.print(f"[yellow]Warning:[/yellow] Extra arguments ignored: {' '.join(input_file[1:])}")
                else:
                    console.print(f"[red]Error:[/red] File not found: {potential_path}")
                    console.print("[yellow]Hint:[/yellow] If your path contains spaces, try using quotes: \"path with spaces/file.srt\"")
                    sys.exit(1)
        else:
            # Single argument
            input_file = input_file[0]
        
        # Generate output filename if not specified
        input_path = Path(input_file)
        if not output_file:
            # Generate output filename in the same directory as input
            output_file = str(input_path.with_suffix('.wav'))
            console.print(f"[cyan]Output file:[/cyan] {output_file}")
        
        # Validate output file extension
        output_path = Path(output_file)
        if output_path.suffix.lower() not in ['.wav', '.mp3', '.m4a']:
            console.print("[red]Error:[/red] Output file must be .wav, .mp3, or .m4a")
            sys.exit(1)
        
        # Parse SRT file
        console.print(f"[cyan]Parsing SRT file:[/cyan] {input_file}")
        parser = SRTParser()
        
        try:
            entries = parser.parse_file(input_file)
        except Exception as e:
            console.print(f"[red]Error parsing SRT file:[/red] {str(e)}")
            sys.exit(1)
        
        # Show statistics
        stats = parser.get_statistics(entries)
        console.print(f"[green]✓[/green] Found {stats['count']} subtitles")
        console.print(f"  Total duration: {stats['total_duration']:.1f} seconds")
        console.print(f"  Total characters: {stats['total_characters']}")
        
        # Update session statistics
        session.update_stats('total_subtitles', stats['count'])
        
        # Validate entries
        warnings = parser.validate_entries(entries)
        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")
        
        # Preview mode
        if preview:
            entries = entries[:preview]
            console.print(f"\n[yellow]Preview mode:[/yellow] Processing first {len(entries)} subtitles")
        
        # Process with TTS
        audio_stats = process_srt(entries, output_path, config_manager, service_name, logger)
        
        # Display sample entries
        if entries:
            console.print("\n[cyan]Sample entries:[/cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=6)
            table.add_column("Time", width=20)
            table.add_column("Text", width=50)
            
            for entry in entries[:5]:
                table.add_row(
                    str(entry.index),
                    f"{entry.start_time} → {entry.end_time}",
                    entry.content[:50] + "..." if len(entry.content) > 50 else entry.content
                )
            
            console.print(table)
        
        # Display session summary
        if session:
            session.print_summary(console)
        
        # Display cache statistics
        if cache_manager:
            cache_stats = cache_manager.get_statistics()
            if cache_stats['hits'] + cache_stats['misses'] > 0:
                console.print("\n[bold cyan]缓存统计:[/bold cyan]")
                console.print(f"  命中率: {cache_stats['hit_rate']}% ({cache_stats['hits']}/{cache_stats['hits'] + cache_stats['misses']})")
                console.print(f"  缓存大小: {cache_stats.get('total_size_mb', 0)}MB / {cache_stats.get('max_size_mb', 0)}MB")
                console.print(f"  缓存项数: {cache_stats.get('total_entries', 0)}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  正在停止任务处理...[/yellow]")
        # 给一点时间让当前任务完成
        import time
        time.sleep(0.5)
        console.print("[yellow]任务已停止，正在清理服务...[/yellow]")
        # 清理逻辑会由信号处理器自动处理
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {str(e)}")
        if debug:
            console.print_exception()
        # 清理逻辑会由信号处理器自动处理
        sys.exit(1)


def list_available_services(config_manager: ConfigManager):
    """List all available TTS services."""
    services = config_manager.get_enabled_services()
    
    if not services:
        console.print("[yellow]No TTS services configured[/yellow]")
        return
    
    table = Table(title="Available TTS Services", show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan", width=12)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Voice", width=25)
    table.add_column("Language", width=10)
    
    for name, config in services.items():
        status = "[green]Enabled[/green]" if config.enabled else "[red]Disabled[/red]"
        voice = config.voice_settings.name or config.voice_settings.gender
        
        table.add_row(
            name,
            str(config.priority),
            status,
            voice,
            config.voice_settings.language
        )
    
    console.print(table)


def process_srt(entries, output_path, config_manager, service_name, logger):
    """Process SRT entries with TTS service."""
    # Get service with fallback support
    tts_service, actual_service_name = get_tts_service_with_fallback(
        config_manager, service_name, logger
    )
    
    if not tts_service:
        console.print("[red]Error:[/red] No available TTS services")
        sys.exit(1)
    
    console.print(f"\n[cyan]Using TTS service:[/cyan] {actual_service_name}")
    
    # Initialize audio processor with config
    audio_processor = AudioProcessor(
        output_format=output_path.suffix[1:],
        config=config_manager.config.audio_processing
    )
    
    # Convert entries to the format expected by process_subtitles
    subtitles = []
    for entry in entries:
        subtitles.append({
            'index': entry.index,
            'start': entry.start_time,
            'end': entry.end_time,
            'content': entry.content
        })
    
    # Create a wrapper for TTS service that shows progress
    class ProgressTTSWrapper:
        def __init__(self, tts_service, progress_callback):
            self.tts_service = tts_service
            self.progress_callback = progress_callback
            # Copy all attributes from the wrapped service
            for attr in dir(tts_service):
                if not attr.startswith('_') and attr not in ['text_to_speech', 'text_to_speech_with_cache']:
                    setattr(self, attr, getattr(tts_service, attr))
            
            # Also copy _first_segment_path for GPT-SoVITS
            if hasattr(tts_service, '_first_segment_path'):
                self._first_segment_path = tts_service._first_segment_path
        
        def text_to_speech(self, text, save_as_reference=False, speed_factor=None):
            # Call the original method
            if hasattr(self.tts_service, '_first_segment_path'):
                # GPT-SoVITS service - doesn't support speed_factor in text_to_speech
                result = self.tts_service.text_to_speech(text, save_as_reference)
            else:
                # Other services
                result = self.tts_service.text_to_speech(text)
            # Update progress
            self.progress_callback(text)
            return result
        
        def text_to_speech_with_cache(self, text):
            result = self.tts_service.text_to_speech_with_cache(text)
            self.progress_callback(text)
            return result
    
    # Process all subtitles with the new method
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Converting subtitles to speech...", total=len(entries))
        processed_count = [0]  # Use list to allow modification in closure
        
        def update_progress(text):
            processed_count[0] += 1
            progress.update(task, advance=1, description=f"Processing: {text[:30]}...")
        
        # Wrap TTS service with progress tracking
        wrapped_service = ProgressTTSWrapper(tts_service, update_progress)
        
        # Process with new method with fallback support
        final_audio = process_subtitles_with_fallback(
            audio_processor, 
            subtitles, 
            wrapped_service, 
            config_manager, 
            logger,
            update_progress
        )
    
    # Save final audio
    console.print("\n[cyan]Generating final audio...[/cyan]")
    try:
        audio_processor.save_audio(final_audio, output_path)
        console.print(f"\n[green]✓ Success![/green] Audio saved to: {output_path}")
        
        # Display processing statistics
        processing_stats = audio_processor.get_processing_statistics()
        if processing_stats['split_segments'] > 0 or processing_stats['speed_adjusted'] > 0 or processing_stats.get('over_duration', 0) > 0:
            console.print("\n[yellow]⚠️  Audio Processing Statistics:[/yellow]")
            console.print(f"  • Total segments: {processing_stats['total_segments']}")
            
            if processing_stats.get('text_optimized', 0) > 0:
                console.print(f"  • Text optimized: {processing_stats['text_optimized']} segments")
                console.print(f"  • Max optimization level: {processing_stats['max_optimization_level']}")
            
            if processing_stats.get('over_duration', 0) > 0:
                console.print(f"  • Slightly over duration: {processing_stats['over_duration']} (preserved complete audio)")
            
        # Update session statistics
        session = get_current_session()
        if session:
            session.update_stats('processed_subtitles', len(entries))
            session.update_stats('text_optimizations', processing_stats.get('text_optimized', 0))
            if processing_stats.get('text_optimized', 0) > 0:
                session.update_stats('max_optimization_level', processing_stats['max_optimization_level'])
            
        return processing_stats
            
    except Exception as e:
        console.print(f"[red]Error saving audio:[/red] {str(e)}")
        sys.exit(1)


def get_tts_service_with_fallback(config_manager, preferred_service, logger):
    """Get TTS service with automatic fallback.
    
    Args:
        config_manager: Configuration manager instance
        preferred_service: User-specified service name (optional)
        logger: Logger instance
        
    Returns:
        tuple: (service_instance, service_name) or (None, None) if no service available
    """
    # If user specified a service, try it first
    if preferred_service:
        if preferred_service not in config_manager.config.services:
            console.print(f"[yellow]Warning:[/yellow] Unknown service '{preferred_service}'")
        else:
            service = try_initialize_service(preferred_service, config_manager, logger)
            if service:
                return service, preferred_service
            console.print(f"[yellow]Warning:[/yellow] Service '{preferred_service}' not available")
    
    # Try services by priority
    services = config_manager.get_enabled_services()
    if not services:
        return None, None
    
    for service_name in services:
        console.print(f"[cyan]Trying service:[/cyan] {service_name}...")
        service = try_initialize_service(service_name, config_manager, logger)
        if service:
            if service_name != preferred_service:
                console.print(f"[yellow]Info:[/yellow] Using fallback service '{service_name}'")
            return service, service_name
    
    return None, None


def get_enabled_services(config_manager):
    """Get all enabled TTS services sorted by priority.
    
    Returns:
        List of service info dicts with 'name' and 'priority'
    """
    services = []
    for service_name, service_config in config_manager.config.services.items():
        if hasattr(service_config, 'enabled') and service_config.enabled:
            services.append({
                'name': service_name,
                'priority': getattr(service_config, 'priority', 999)
            })
    
    # Sort by priority (lower number = higher priority)
    return sorted(services, key=lambda x: x['priority'])


def process_subtitles_with_fallback(audio_processor, subtitles, tts_service, config_manager, logger, progress_callback):
    """Process subtitles with automatic service fallback on audio length errors.
    
    Args:
        audio_processor: Audio processor instance
        subtitles: List of subtitle dictionaries
        tts_service: Current TTS service (wrapped with progress)
        config_manager: Configuration manager for getting fallback services
        logger: Logger instance
        progress_callback: Progress update callback function
        
    Returns:
        AudioSegment: Final processed audio
    """
    current_service = tts_service
    failed_services = set()
    
    # Get the original service name (before wrapping)
    original_service_name = getattr(tts_service.tts_service, 'name', 'unknown')
    
    while True:
        try:
            # Attempt to process subtitles with current service
            return audio_processor.process_subtitles(subtitles, current_service)
            
        except AudioTooLongError as e:
            # Mark this service as failed
            failed_services.add(original_service_name)
            
            logger.warning(
                f"Service '{original_service_name}' failed due to audio length issue: "
                f"{e.actual_duration:.2f}s vs {e.target_duration:.2f}s (ratio: {e.duration_ratio:.2f}x)"
            )
            console.print(
                f"\n[yellow]⚠️  Audio too long with '{original_service_name}' service[/yellow]\n"
                f"[yellow]   Attempting fallback to next available service...[/yellow]"
            )
            
            # Get all enabled services sorted by priority
            enabled_services = get_enabled_services(config_manager)
            
            # Find next available service
            next_service = None
            for service_info in enabled_services:
                service_name = service_info['name']
                if service_name not in failed_services:
                    logger.info(f"Attempting to use fallback service: {service_name}")
                    new_service = try_initialize_service(service_name, config_manager, logger)
                    if new_service:
                        next_service = new_service
                        original_service_name = service_name
                        break
            
            if not next_service:
                # No more services available
                logger.error("No more TTS services available for fallback")
                console.print("[red]✗ Error:[/red] All TTS services failed. Unable to process audio.")
                raise RuntimeError(
                    f"Audio generation failed: All services exhausted. "
                    f"Last error - Audio too long: {e.actual_duration:.2f}s vs {e.target_duration:.2f}s"
                )
            
            # Wrap the new service with progress tracking
            current_service = ProgressTTSWrapper(next_service, progress_callback)
            console.print(f"[green]✓ Switched to '{original_service_name}' service[/green]")
            
            # Reset audio processor to start fresh with new service
            audio_processor.audio_segments.clear()
            audio_processor.processing_stats = ProcessingStatistics()


def try_initialize_service(service_name, config_manager, logger):
    """Try to initialize a TTS service.
    
    Args:
        service_name: Name of the service to initialize
        config_manager: Configuration manager instance
        logger: Logger instance
        
    Returns:
        TTSService instance or None if initialization failed
    """
    if service_name not in TTS_SERVICES:
        logger.warning(f"Service '{service_name}' not registered")
        return None
    
    service_config = config_manager.config.services.get(service_name)
    if not service_config or not service_config.enabled:
        logger.debug(f"Service '{service_name}' not enabled")
        return None
    
    service_class = TTS_SERVICES[service_name]
    
    try:
        # Initialize service
        service = service_class(service_config.model_dump())
        
        # Check health
        if hasattr(service, 'check_health') and not service.check_health():
            logger.warning(f"Service '{service_name}' health check failed")
            # 清理已创建的服务实例
            if hasattr(service, '_cleanup'):
                service._cleanup()
            return None
        
        return service
        
    except Exception as e:
        logger.warning(f"Failed to initialize '{service_name}': {str(e)}")
        # 如果服务实例已创建，需要清理
        if 'service' in locals() and hasattr(service, '_cleanup'):
            service._cleanup()
        return None


if __name__ == '__main__':
    main()