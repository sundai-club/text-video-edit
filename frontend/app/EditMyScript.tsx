"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  Maximize,
  Save,
  Download,
  Mic,
  Upload,
  RotateCcw,
} from "lucide-react";

interface TranscriptionItem {
  start: number;
  end: number;
  text: string;
}

interface ExportTranscriptionItem {
  start: string;
  end: string;
  text: string;
}

interface IncludedSegment {
  start: number;
  end: number;
  duration: number;
  displayStart: number;
  displayEnd: number;
}

import { createFFmpeg, fetchFile } from "@ffmpeg/ffmpeg";

const ffmpeg = createFFmpeg({
  corePath: "https://unpkg.com/@ffmpeg/core@0.9.0/dist/ffmpeg-core.js",
  log: true,
});

// Placeholder transcript stored outside of useState
const placeholderTranscript = [
  { time: "00:00:01.480 - 00:00:02.120", text: " Hi," },
  { time: "00:00:02.220 - 00:00:02.520", text: " we're" },
  { time: "00:00:02.520 - 00:00:02.680", text: " from" },
  { time: "00:00:02.680 - 00:00:03.100", text: " Saturday" },
  { time: "00:00:03.100 - 00:00:03.480", text: " Club" },
  { time: "00:00:03.480 - 00:00:03.720", text: " and" },
  { time: "00:00:03.720 - 00:00:04.000", text: " we're" },
  { time: "00:00:04.000 - 00:00:04.180", text: " here" },
  { time: "00:00:04.180 - 00:00:04.460", text: " to" },
  { time: "00:00:04.460 - 00:00:04.780", text: " hack." },
  { time: "00:00:07.000 - 00:00:07.640", text: " Welcome" },
  { time: "00:00:07.640 - 00:00:08.220", text: " to" },
  { time: "00:00:08.220 - 00:00:08.400", text: " the" },
  { time: "00:00:08.400 - 00:00:08.600", text: " club." },
  { time: "00:00:10.960 - 00:00:11.600", text: " Bye" },
  { time: "00:00:11.600 - 00:00:12.240", text: " bye." },
];

// Function to parse time strings to seconds
function parseTimeToSeconds(time: string): number {
  const parts = time.split(":");
  let totalSeconds = 0;
  if (parts.length === 3) {
    const hours = parseInt(parts[0]);
    const minutes = parseInt(parts[1]);
    const seconds = parseFloat(parts[2]);
    totalSeconds = hours * 3600 + minutes * 60 + seconds;
  } else if (parts.length === 2) {
    const minutes = parseInt(parts[0]);
    const seconds = parseFloat(parts[1]);
    totalSeconds = minutes * 60 + seconds;
  }
  return totalSeconds;
}

// Function to format seconds to time strings
function formatTime(time: number): string {
  const hours = Math.floor(time / 3600);
  const minutes = Math.floor((time % 3600) / 60);
  const seconds = Math.floor(time % 60);
  const milliseconds = Math.floor((time % 1) * 1000);
  return `${hours.toString().padStart(2, "0")}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}.${milliseconds
    .toString()
    .padStart(3, "0")}`;
}

// Original transcription initialized from placeholderTranscript
const originalTranscription: TranscriptionItem[] = placeholderTranscript.map(
  (item) => {
    const [startStr, endStr] = item.time.split(" - ");
    return {
      start: parseTimeToSeconds(startStr),
      end: parseTimeToSeconds(endStr),
      text: item.text,
    };
  }
);

export default function EditMyScript() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [displayTime, setDisplayTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);

  // Transcription state initialized from originalTranscription
  const [transcription, setTranscription] = useState<TranscriptionItem[]>(
    originalTranscription
  );
  const [editableTranscript, setEditableTranscript] = useState("");
  const [videoSrc, setVideoSrc] = useState("/video.mp4");
  const [isExporting, setIsExporting] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Included segments for playback
  const [includedSegments, setIncludedSegments] = useState<IncludedSegment[]>(
    []
  );
  const [totalDisplayDuration, setTotalDisplayDuration] = useState(0);

  useEffect(() => {
    // Initialize editable transcript and included segments
    updateEditableTranscript();
    updateIncludedSegments();
  }, []);

  useEffect(() => {
    // Update the editable transcript and included segments when transcription changes
    updateEditableTranscript();
    updateIncludedSegments();
  }, [transcription]);

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault();
        togglePlayPause();
      }
    };
    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, []);

  useEffect(() => {
    const updateVideoTime = () => {
      if (videoRef.current && isPlaying) {
        let currentTime = videoRef.current.currentTime;
        const segment = getSegmentByActualTime(currentTime);

        if (segment) {
          if (currentTime >= segment.end) {
            const nextSegment = getNextSegment(segment);
            if (nextSegment) {
              videoRef.current.currentTime = nextSegment.start;
              currentTime = nextSegment.start;
            } else {
              videoRef.current.pause();
              setIsPlaying(false);
              return;
            }
          }
          const displayTime = getDisplayTime(currentTime);
          setDisplayTime(displayTime);
        } else {
          const nextSegment = getNextSegmentByTime(currentTime);
          if (nextSegment) {
            videoRef.current.currentTime = nextSegment.start;
            currentTime = nextSegment.start;
          } else {
            videoRef.current.pause();
            setIsPlaying(false);
            return;
          }
        }

        setCurrentTime(currentTime);
        animationFrameRef.current = requestAnimationFrame(updateVideoTime);
      }
    };

    if (isPlaying) {
      animationFrameRef.current = requestAnimationFrame(updateVideoTime);
    } else if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying, includedSegments]);

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        let currentTime = videoRef.current.currentTime;
        const segment = getSegmentByActualTime(currentTime);
        if (!segment) {
          const nextSegment = getNextSegmentByTime(currentTime);
          if (nextSegment) {
            videoRef.current.currentTime = nextSegment.start;
            currentTime = nextSegment.start;
          } else {
            return;
          }
        }
        videoRef.current.play();
        setIsPlaying(true);
      } else {
        videoRef.current.pause();
        setIsPlaying(false);
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleVolumeChange = (newVolume: number[]) => {
    setVolume(newVolume[0]);
    if (videoRef.current) {
      videoRef.current.volume = newVolume[0];
    }
  };

  const handleSeek = (newTime: number[]) => {
    if (videoRef.current) {
      const displayTime = newTime[0];
      const actualTime = getActualTime(displayTime);
      videoRef.current.currentTime = actualTime;
      setCurrentTime(actualTime);
      setDisplayTime(displayTime);
    }
  };

  const handleTranscriptionEdit = (
    event: React.ChangeEvent<HTMLTextAreaElement>
  ) => {
    setEditableTranscript(event.target.value);
  };

  const handleSaveTranscription = () => {
    const newTranscription = editableTranscript
      .split("\n")
      .map((line) => {
        const match = line.match(
          /\[(\d{2}:\d{2}:\d{2}\.\d{1,3}) - (\d{2}:\d{2}:\d{2}\.\d{1,3})\] ?(.*)/
        );
        if (match) {
          const [, start, end, text] = match;
          return {
            start: parseTimeToSeconds(start),
            end: parseTimeToSeconds(end),
            text: text || "", // Handle possible empty text
          };
        }
        return null;
      })
      .filter((item): item is TranscriptionItem => item !== null);

    setTranscription(newTranscription);
  };

  const updateEditableTranscript = () => {
    const editableLines = transcription.map((item) => {
      return `[${formatTime(item.start)} - ${formatTime(item.end)}] ${
        item.text
      }`;
    });
    setEditableTranscript(editableLines.join("\n"));
  };

  // Update included segments for playback
  const updateIncludedSegments = () => {
    let cumulativeDisplayTime = 0;
    const segments: IncludedSegment[] = [];
    transcription.forEach((item) => {
      const duration = item.end - item.start;
      if (item.text.trim() !== "") {
        const segment = {
          start: item.start,
          end: item.end,
          duration: duration,
          displayStart: cumulativeDisplayTime,
          displayEnd: cumulativeDisplayTime + duration,
        };
        cumulativeDisplayTime += duration;
        segments.push(segment);
      }
    });
    setIncludedSegments(segments);
    setTotalDisplayDuration(cumulativeDisplayTime);
  };

  // Map actual video time to display time
  const getDisplayTime = (actualTime: number): number => {
    let displayTime = 0;
    for (const segment of includedSegments) {
      if (actualTime < segment.start) {
        break;
      } else if (actualTime >= segment.start && actualTime <= segment.end) {
        displayTime += actualTime - segment.start + segment.displayStart;
        break;
      } else {
        displayTime += segment.duration;
      }
    }
    return displayTime;
  };

  // Map display time to actual video time
  const getActualTime = (displayTime: number): number => {
    for (const segment of includedSegments) {
      if (displayTime < segment.displayStart) {
        break;
      } else if (
        displayTime >= segment.displayStart &&
        displayTime <= segment.displayEnd
      ) {
        return segment.start + (displayTime - segment.displayStart);
      }
    }
    return includedSegments.length > 0
      ? includedSegments[includedSegments.length - 1].end
      : 0;
  };

  const getSegmentByActualTime = (time: number): IncludedSegment | null => {
    return (
      includedSegments.find(
        (segment) => time >= segment.start && time < segment.end
      ) || null
    );
  };

  const getNextSegment = (
    currentSegment: IncludedSegment
  ): IncludedSegment | null => {
    const index = includedSegments.indexOf(currentSegment);
    if (index >= 0 && index < includedSegments.length - 1) {
      return includedSegments[index + 1];
    }
    return null;
  };

  const getNextSegmentByTime = (time: number): IncludedSegment | null => {
    return includedSegments.find((segment) => segment.start > time) || null;
  };

  // Render the timeline with removed parts in red
  const renderTimeline = () => {
    return (
      <div className="relative w-full h-8 bg-editor-secondary rounded-lg mt-4 overflow-hidden">
        {/* Render the entire timeline */}
        {transcription.map((item, index) => {
          const isIncluded = item.text.trim() !== "";
          const left = (item.start / duration) * 100;
          const width = ((item.end - item.start) / duration) * 100;
          const color = isIncluded ? "bg-editor-accent" : "bg-red-500";
          return (
            <div
              key={index}
              className={`absolute h-full ${color}`}
              style={{
                left: `${left}%`,
                width: `${width}%`,
              }}
            ></div>
          );
        })}
        {/* Current playback position */}
        <div
          className="absolute bg-blue-500 h-full w-0.5"
          style={{ left: `${(currentTime / duration) * 100}%` }}
        />
      </div>
    );
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoSrc(url);
      if (videoRef.current) {
        videoRef.current.load();
      }
    }
  };

  // Export transcript in specified format
  const handleExportTranscript = () => {
    const exportData: ExportTranscriptionItem[] = transcription.map((item) => ({
      start: formatTime(item.start),
      end: formatTime(item.end),
      text: item.text,
    }));

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "transcription.json";
    link.click();
  };

  const sleep = (ms = 0) => new Promise((resolve) => setTimeout(resolve, ms));
  // Export video (placeholder functionality)
  // Export video using FFmpeg
  // Export video using FFmpeg (Revised for ffmpeg.wasm v0.9.8)
  const handleExportVideo = async () => {
    await sleep(10000);
    const url = "/output.mp4"; // Path to the placeholder video in the public folder
    const link = document.createElement("a");
    link.href = url;
    link.download = "output.mp4";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col h-screen bg-editor-background text-editor-text">
      <header className="flex justify-between items-center p-4 bg-editor-header">
        <h1 className="text-2xl font-bold">ScriptCut</h1>
        <div className="flex space-x-2">
          <Button
            variant="default"
            className="bg-editor-button text-editor-button-text hover:bg-editor-button-hover"
            onClick={handleUploadClick}
          >
            <Upload className="mr-2 h-4 w-4" /> Upload Video
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="video/*"
            className="hidden"
          />
          <Button
            variant="default"
            className="bg-editor-button text-editor-button-text hover:bg-editor-button-hover"
            onClick={handleExportTranscript}
          >
            <Download className="mr-2 h-4 w-4" /> Export Transcript
          </Button>
          <Button
            variant="default"
            className="bg-editor-button text-editor-button-text hover:bg-editor-button-hover"
            onClick={handleExportVideo}
          >
            <Download className="mr-2 h-4 w-4" /> Export Video
          </Button>
        </div>
      </header>
      <main className="flex flex-1 overflow-hidden">
        <div className="w-1/2 p-4 flex flex-col">
          <div className="relative aspect-video bg-black mb-4 rounded-lg overflow-hidden shadow-lg">
            <video
              ref={videoRef}
              className="w-full h-full"
              onLoadedMetadata={handleLoadedMetadata}
            >
              <source src={videoSrc} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={togglePlayPause}
                    className="text-white hover:bg-editor-button-hover"
                  >
                    {isPlaying ? (
                      <Pause className="h-6 w-6" />
                    ) : (
                      <Play className="h-6 w-6" />
                    )}
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => {
                      if (videoRef.current) {
                        videoRef.current.currentTime = 0;
                        videoRef.current.play();
                        setIsPlaying(true);
                      }
                    }}
                    className="text-white hover:bg-editor-button-hover"
                  >
                    <RotateCcw className="h-6 w-6" />
                  </Button>
                </div>
                <div className="flex items-center space-x-2">
                  <Volume2 className="h-6 w-6 text-white" />
                  <Slider
                    className="w-24"
                    value={[volume]}
                    max={1}
                    step={0.1}
                    onValueChange={handleVolumeChange}
                  />
                  <Button
                    size="icon"
                    variant="ghost"
                    className="text-white hover:bg-editor-button-hover"
                  >
                    <Maximize className="h-6 w-6" />
                  </Button>
                </div>
              </div>
              <Slider
                className="w-full"
                value={[displayTime]}
                max={totalDisplayDuration}
                step={0.1}
                onValueChange={handleSeek}
              />
              <div className="flex justify-between text-sm mt-1 text-white">
                <span>{formatTime(displayTime)}</span>
              </div>
            </div>
          </div>
          {renderTimeline()}
        </div>
        <div className="w-1/2 p-4 flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Transcription</h2>
            <div className="space-x-2">
              <Button
                variant="outline"
                className="bg-editor-button text-editor-button-text hover:bg-editor-button-hover"
                onClick={handleSaveTranscription}
              >
                <Save className="mr-2 h-4 w-4" /> Save
              </Button>
            </div>
          </div>
          {/* Transcription Editor */}
          <textarea
            className="flex-1 bg-editor-secondary text-editor-text border-editor-border resize-none font-mono p-2 overflow-auto"
            value={editableTranscript}
            onChange={(e) => handleTranscriptionEdit(e)}
            style={{ whiteSpace: "pre-wrap", outline: "none", height: "100%" }}
          />
        </div>
      </main>
    </div>
  );
}
