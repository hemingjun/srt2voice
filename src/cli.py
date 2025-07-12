import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from .config import ConfigManager
from .parser.srt import SRTParser
from .utils.logger import setup_logger
from .tts import GoogleTTSService
from .audio import AudioProcessor
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

console = Console()


@click.command()
@click.option('-i', '--input', 'input_file', type=click.Path(exists=True),
              help='Input SRT file path')
@click.option('-o', '--output', 'output_file',
              help='Output audio file path')
@click.option('-c', '--config', 'config_path', 
              default='config/default.yaml',
              help='Configuration file path')
@click.option('-s', '--service', 'service_name',
              help='TTS service to use (e.g., google, azure)')
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
        srt2speech -i input.srt -o output.wav
        srt2speech -i input.srt -o output.wav --service google
        srt2speech -i input.srt -o output.wav --preview 5
        srt2speech --list-services
    """
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        
        # Setup logging
        log_level = 'DEBUG' if debug else config_manager.config.logging['level']
        logger = setup_logger('srt2speech', log_level)
        
        # List services and exit if requested
        if list_services:
            list_available_services(config_manager)
            return
        
        # Validate required arguments for processing
        if not input_file:
            console.print("[red]Error:[/red] Input file is required. Use -i/--input to specify the SRT file.")
            sys.exit(1)
        
        if not output_file:
            console.print("[red]Error:[/red] Output file is required. Use -o/--output to specify the output audio file.")
            sys.exit(1)
        
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
        process_srt(entries, output_path, config_manager, service_name, logger)
        
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
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {str(e)}")
        if debug:
            console.print_exception()
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
    # Determine which service to use
    if service_name:
        if service_name not in config_manager.config.tts_services:
            console.print(f"[red]Error:[/red] Unknown service '{service_name}'")
            sys.exit(1)
        tts_config = config_manager.config.tts_services[service_name]
    else:
        # Use the highest priority enabled service
        services = config_manager.get_enabled_services()
        if not services:
            console.print("[red]Error:[/red] No TTS services enabled")
            sys.exit(1)
        service_name = list(services.keys())[0]
        tts_config = services[service_name]
    
    console.print(f"\n[cyan]Using TTS service:[/cyan] {service_name}")
    
    # Initialize TTS service (currently only Google is implemented)
    if service_name != 'google':
        console.print(f"[red]Error:[/red] Service '{service_name}' not yet implemented")
        sys.exit(1)
    
    # Convert config to dict for TTS service
    tts_service_config = {
        'api_key_path': tts_config.api_key_path,
        'language_code': tts_config.voice_settings.language,
        'voice_name': tts_config.voice_settings.name,
        'speaking_rate': tts_config.voice_settings.speed,
        'pitch': tts_config.voice_settings.pitch
    }
    
    try:
        tts_service = GoogleTTSService(tts_service_config)
    except Exception as e:
        console.print(f"[red]Error initializing TTS service:[/red] {str(e)}")
        sys.exit(1)
    
    # Initialize audio processor
    audio_processor = AudioProcessor(output_format=output_path.suffix[1:])
    
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
                # Generate audio for this subtitle
                audio = tts_service.text_to_speech(entry.content)
                
                # Add to processor
                audio_processor.add_audio_segment(
                    entry.start.total_seconds(),
                    audio
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
    except Exception as e:
        console.print(f"[red]Error saving audio:[/red] {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()