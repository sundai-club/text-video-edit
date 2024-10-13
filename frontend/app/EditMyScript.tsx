"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
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
} from "lucide-react";

interface TranscriptionItem {
  start: number;
  end: number;
  text: string;
}

export default function EditMyScript() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [transcription, setTranscription] = useState<TranscriptionItem[]>([
    { start: 0, end: 5, text: "Welcome to EditMyScript." },
    {
      start: 5,
      end: 10,
      text: "This is an AI-powered video editing platform.",
    },
    {
      start: 10,
      end: 15,
      text: "Edit your video by simply modifying the script.",
    },
    {
      start: 15,
      end: 20,
      text: "Our AI will take care of the rest, including voice synthesis.",
    },
  ]);
  const [editableTranscript, setEditableTranscript] = useState("");
  const [videoSrc, setVideoSrc] = useState("/video.mp4");
  const [isExporting, setIsExporting] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setEditableTranscript(
      transcription
        .map(
          (item) =>
            `[${formatTime(item.start)} - ${formatTime(item.end)}] ${item.text}`
        )
        .join("\n")
    );
  }, [transcription]);

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        togglePlayPause();
      }
    };
    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, []);

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play();
      } else {
        videoRef.current.pause();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
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
      videoRef.current.currentTime = newTime[0];
      setCurrentTime(newTime[0]);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}`;
  };

  const handleTranscriptionEdit = (newText: string) => {
    setEditableTranscript(newText);
    // Here you would typically call an API to update the video based on the new transcription
  };

  const handleSaveTranscription = () => {
    // Parse the editable transcript and update the transcription state
    const newTranscription = editableTranscript
      .split("\n")
      .map((line) => {
        const match = line.match(/\[(\d{2}:\d{2}) - (\d{2}:\d{2})\] (.+)/);
        if (match) {
          const [, start, end, text] = match;
          return {
            start: parseTimeToSeconds(start),
            end: parseTimeToSeconds(end),
            text,
          };
        }
        return null;
      })
      .filter((item): item is TranscriptionItem => item !== null);

    setTranscription(newTranscription);
  };

  const parseTimeToSeconds = (time: string): number => {
    const [minutes, seconds] = time.split(":").map(Number);
    return minutes * 60 + seconds;
  };

  const renderTimeline = () => {
    return (
      <div className="relative w-full h-8 bg-editor-secondary rounded-lg mt-4 overflow-hidden">
        {transcription.map((item, index) => (
          <div
            key={index}
            className="absolute h-full bg-editor-accent hover:bg-editor-accent-hover transition-colors cursor-pointer"
            style={{
              left: `${(item.start / duration) * 100}%`,
              width: `${((item.end - item.start) / duration) * 100}%`,
            }}
            onClick={() => handleSeek([item.start])}
          />
        ))}
        <div
          className="absolute h-full w-0.5 bg-editor-highlight"
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

  const handleExport = async () => {
    setIsExporting(true);
    try {
      // Simulate export process
      await new Promise((resolve) => setTimeout(resolve, 3000));

      // Create a blob with the transcription data
      const transcriptionBlob = new Blob(
        [JSON.stringify(transcription, null, 2)],
        {
          type: "application/json",
        }
      );

      // Create a download link for the transcription
      const transcriptionUrl = URL.createObjectURL(transcriptionBlob);
      const transcriptionLink = document.createElement("a");
      transcriptionLink.href = transcriptionUrl;
      transcriptionLink.download = "transcription.json";

      // Trigger download for transcription
      transcriptionLink.click();

      // Create a download link for the video
      const videoLink = document.createElement("a");
      videoLink.href = videoSrc;
      videoLink.download = "edited_video.mp4";

      // Trigger download for video
      videoLink.click();
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-editor-background text-editor-text">
      <header className="flex justify-between items-center p-4 bg-editor-header">
        <h1 className="text-2xl font-bold">EditMyScript</h1>
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
            onClick={handleExport}
            disabled={isExporting}
          >
            <Download className="mr-2 h-4 w-4" />
            {isExporting ? "Exporting..." : "Export"}
          </Button>
        </div>
      </header>
      <main className="flex flex-1 overflow-hidden">
        <div className="w-1/2 p-4 flex flex-col">
          <div className="relative aspect-video bg-black mb-4 rounded-lg overflow-hidden shadow-lg">
            <video
              ref={videoRef}
              className="w-full h-full"
              onTimeUpdate={handleTimeUpdate}
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
                    className="text-white hover:bg-editor-button-hover"
                  >
                    <SkipBack className="h-6 w-6" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="text-white hover:bg-editor-button-hover"
                  >
                    <SkipForward className="h-6 w-6" />
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
                value={[currentTime]}
                max={duration}
                step={0.1}
                onValueChange={handleSeek}
              />
              <div className="flex justify-between text-sm mt-1 text-white">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
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
              <Button
                variant="outline"
                className="bg-editor-button text-editor-button-text hover:bg-editor-button-hover"
              >
                <Mic className="mr-2 h-4 w-4" /> Replace Voice
              </Button>
            </div>
          </div>
          <Textarea
            value={editableTranscript}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
              handleTranscriptionEdit(e.target.value)
            }
            className="flex-1 bg-editor-secondary text-editor-text border-editor-border resize-none font-mono"
            placeholder="Edit your transcription here..."
          />
        </div>
      </main>
    </div>
  );
}
