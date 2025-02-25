import { useState } from "react";
import axios from "axios";
import { Upload, File, Download, Loader2 } from "lucide-react";
import styles from "./App.module.css";

const API_BASE_URL = "http://localhost:5000";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [videoURL, setVideoURL] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string>(""); 
  const [wordCount, setWordCount] = useState<number>(0);
  const [downloadLink, setDownloadLink] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false); 
  const [loading, setLoading] = useState<boolean>(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      const selectedFile = event.target.files[0];
      setFile(selectedFile);
      setVideoURL(URL.createObjectURL(selectedFile));
    }
  };

  const handleUpload = async () => {
    if (!file) return alert("Please select a video file");

    setIsProcessing(true); // Start processing
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.transcript) {
        setTranscript(response.data.transcript);
        setWordCount(response.data.transcript.split(/\s+/).length);
        setDownloadLink(`${API_BASE_URL}/download/${response.data.download_link}`);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
    } finally {
      setIsProcessing(false); // Reset processing state after completion
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h1>🎬 Video to Transcript Converter</h1>
      <br />

      <div className={styles.uploadSection}>
        <label className={styles.fileInputLabel}>
          <File size={20} /> Browse File
          <input type="file" accept=".mp4,.mov" onChange={handleFileChange} hidden />
        </label>
        <button
          className={styles.uploadButton}
          onClick={handleUpload}
          disabled={!file || loading || isProcessing}
        >
          {loading ? <Loader2 className={styles.spinner} size={20} /> : <Upload size={20} />}
          {loading ? "Transcribing..." : isProcessing ? "Processing..." : "Upload & Transcribe"}
        </button>
      </div>

      {loading && <div className={styles.loadingContainer}>Transcribing... Please wait</div>}

      <div className={styles.contentContainer}>
        {videoURL && (
          <div className={styles.videoContainer}>
            <video className={styles.videoPlayer} controls>
              <source src={videoURL} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        )}

        {transcript && !loading && (
          <div className={styles.transcriptContainer}>
            <h3>📜 Transcript:</h3>
            <p className={styles.transcriptText}>{transcript}</p>
            <h4>🔢 Word Count: {wordCount}</h4>
            <a href={downloadLink} download className={styles.downloadButton}>
              <Download size={20} /> Download Transcript
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;