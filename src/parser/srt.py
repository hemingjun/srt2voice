import srt
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import timedelta


class SubtitleEntry(BaseModel):
    index: int = Field(ge=1, description="Subtitle index")
    start_time: timedelta = Field(description="Start time")
    end_time: timedelta = Field(description="End time")
    content: str = Field(min_length=1, description="Subtitle content")
    
    @validator('end_time')
    def validate_time_order(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()


class SRTParser:
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
    
    def parse_file(self, file_path: str) -> List[SubtitleEntry]:
        """Parse SRT file and return list of subtitle entries."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"SRT file not found: {file_path}")
        
        if not path.suffix.lower() == '.srt':
            raise ValueError(f"Not an SRT file: {file_path}")
        
        try:
            with open(path, 'r', encoding=self.encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for enc in ['utf-8-sig', 'gbk', 'gb2312', 'big5']:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        content = f.read()
                    self.encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Unable to decode SRT file with common encodings")
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[SubtitleEntry]:
        """Parse SRT content string and return list of subtitle entries."""
        try:
            subtitles = list(srt.parse(content))
        except Exception as e:
            raise ValueError(f"Invalid SRT format: {str(e)}")
        
        if not subtitles:
            raise ValueError("No subtitles found in file")
        
        entries = []
        for sub in subtitles:
            # Clean up content
            content = sub.content.strip()
            content = content.replace('\n', ' ')  # Replace newlines with spaces
            
            if not content:
                continue
            
            entry = SubtitleEntry(
                index=sub.index,
                start_time=sub.start,
                end_time=sub.end,
                content=content
            )
            entries.append(entry)
        
        return entries
    
    def validate_entries(self, entries: List[SubtitleEntry]) -> List[str]:
        """Validate subtitle entries and return list of warnings."""
        warnings = []
        
        if not entries:
            warnings.append("No subtitle entries found")
            return warnings
        
        # Check for overlapping subtitles
        for i in range(len(entries) - 1):
            if entries[i].end_time > entries[i + 1].start_time:
                warnings.append(
                    f"Overlapping subtitles: #{entries[i].index} ends at "
                    f"{entries[i].end_time}, but #{entries[i + 1].index} starts at "
                    f"{entries[i + 1].start_time}"
                )
        
        # Check for very short or very long subtitles
        for entry in entries:
            if entry.duration < 0.1:
                warnings.append(f"Very short subtitle #{entry.index}: {entry.duration:.2f}s")
            elif entry.duration > 10.0:
                warnings.append(f"Very long subtitle #{entry.index}: {entry.duration:.2f}s")
            
            # Check for very long text
            if len(entry.content) > 200:
                warnings.append(
                    f"Very long text in subtitle #{entry.index}: "
                    f"{len(entry.content)} characters"
                )
        
        return warnings
    
    def get_total_duration(self, entries: List[SubtitleEntry]) -> timedelta:
        """Get total duration from first to last subtitle."""
        if not entries:
            return timedelta(0)
        
        return entries[-1].end_time - entries[0].start_time
    
    def get_statistics(self, entries: List[SubtitleEntry]) -> dict:
        """Get statistics about the subtitle entries."""
        if not entries:
            return {
                'count': 0,
                'total_duration': 0.0,
                'average_duration': 0.0,
                'total_characters': 0,
                'average_characters': 0.0
            }
        
        total_duration = sum(entry.duration for entry in entries)
        total_characters = sum(len(entry.content) for entry in entries)
        
        return {
            'count': len(entries),
            'total_duration': total_duration,
            'average_duration': total_duration / len(entries),
            'total_characters': total_characters,
            'average_characters': total_characters / len(entries),
            'first_subtitle_time': str(entries[0].start_time),
            'last_subtitle_time': str(entries[-1].end_time)
        }