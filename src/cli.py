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
@click.option('--emotion', default=None,
              help='Default emotion for all subtitles (neutral, emphasis, friendly, professional)')
@click.option('--emotion-file', 'emotion_file_path',
              help='Path to emotion sequence file (YAML format)')
@click.version_option(version='0.1.0', prog_name='srt2speech')
def main(input_file, output_file, config_path, service_name, preview, debug, list_services, emotion, emotion_file_path):
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
    
    # Process each subtitle with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Converting subtitles to speech...", total=len(entries))
        
        for i, entry in enumerate(entries):
            try:
                # Generate audio for this subtitle (with cache support)
                audio = tts_service.text_to_speech_with_cache(entry.content)
                
                # Calculate timing for overlap detection
                start_time = entry.start_time.total_seconds()
                end_time = entry.end_time.total_seconds()
                next_start_time = None
                
                if i < len(entries) - 1:
                    next_start_time = entries[i + 1].start_time.total_seconds()
                
                # Add to processor with timing info for overlap detection
                audio_processor.add_audio_segment(
                    start_time,
                    audio,
                    end_time=end_time,
                    next_start_time=next_start_time
                )
                
                progress.update(task, advance=1, description=f"Processing: {entry.content[:30]}...")
                
            except Exception as e:
                logger.error(f"Error processing subtitle {entry.index}: {str(e)}")
                console.print(f"[red]Error:[/red] Failed to process subtitle {entry.index}")
                continue
    
    # Generate and save final audio
    console.print("\n[cyan]Generating final audio...[/cyan]")
    try:
        final_audio = audio_processor._concatenate_audio()
        audio_processor.save_audio(final_audio, output_path)
        console.print(f"\n[green]✓ Success![/green] Audio saved to: {output_path}")
        
        # Display overlap statistics if any overlaps were detected
        overlap_stats = audio_processor.get_overlap_statistics()
        if overlap_stats['total_overlaps'] > 0:
            console.print("\n[yellow]⚠️  Audio Overlap Statistics:[/yellow]")
            console.print(f"  • Total overlaps detected: {overlap_stats['total_overlaps']}")
            
            if overlap_stats['speed_adjusted'] > 0:
                console.print(f"  • Speed adjusted: {overlap_stats['speed_adjusted']} (max speed: {overlap_stats['max_speed_factor']}x)")
            
            if overlap_stats['truncated'] > 0:
                console.print(f"  • Truncated with fade: {overlap_stats['truncated']}")
            
            if overlap_stats['warned_only'] > 0:
                console.print(f"  • Warned only (no adjustment): {overlap_stats['warned_only']}")
            
            if overlap_stats['total_time_adjusted'] > 0:
                console.print(f"  • Total time adjusted: {overlap_stats['total_time_adjusted']:.1f} seconds")
            
            # Show current handling strategy
            overlap_handling = config_manager.config.audio_processing.get('overlap_handling', 'speed_adjust')
            console.print(f"\n  Current strategy: [cyan]{overlap_handling}[/cyan]")
            console.print("  (Change in config/default.yaml → audio_processing.overlap_handling)")
            
        # Update session statistics
        session = get_current_session()
        if session:
            session.update_stats('processed_subtitles', len(entries))
            session.update_stats('audio_adjustments', overlap_stats['total_overlaps'])
            if overlap_stats['speed_adjusted'] > 0:
                session.update_stats('speed_adjustments', overlap_stats['max_speed_factor'])
            
        return overlap_stats
            
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