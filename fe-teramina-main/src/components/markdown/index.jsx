import { Fragment, useState } from "react";
import { Card, CardContent, Typography, Button } from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useStyles } from "components/markdown/styles";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";

export const Markdown = ({ data }) => {
  const [messages, setMessages] = useState([]);
  const [buttonText, setButtonText] = useState("Generate Summary");
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);
  const [isSummaryGenerated, setIsSummaryGenerated] = useState(false);
  const { classes: styles } = useStyles();

  const generateSummary = async () => {
    try {
      setButtonText("Generating...");
      setIsButtonDisabled(true);

      const response = await fetch(`${import.meta.env.VITE_TERAMINA_LLM_API}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": import.meta.env.VITE_TERAMINA_API_KEY,
        },
        body: JSON.stringify({
          question: data.prompt_summary,
          model: import.meta.env.VITE_SUMMARY_MODEL,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const responseData = await response.json();
      const taskId = responseData.task_id;

      // Step 2: Polling untuk mengecek status task
      let taskStatus = "processing";
      let result = null;

      while (taskStatus !== "completed") {
        await new Promise((resolve) => setTimeout(resolve, 10000)); // Wiat 10 detik sebelum cek lagi

        const statusResponse = await fetch(
          `${import.meta.env.VITE_TERAMINA_LLM_API}/api/chat/result/${taskId}`, // API untuk cek status task
          {
            method: "GET",
            headers: {
              "x-api-key": import.meta.env.VITE_TERAMINA_API_KEY,
            },
          }
        );

        if (!statusResponse.ok) {
          throw new Error("Failed to fetch task status.");
        }

        const statusData = await statusResponse.json();
        taskStatus = statusData.status;
        result = statusData.response; // Ambil hasil jika tersedia
      }

      // Update the card content with the API response
      setMessages([result.answer || "No summary available."]);
      setIsSummaryGenerated(true);

      // Update button text after successful generation
      setButtonText("Summary Generated");
    } catch (error) {
      setMessages(["Error generating summary. Please try again."]);
      setButtonText("Try Again");
    } finally {
      // Re-enable the button after the request is complete
      setIsButtonDisabled(false);
    }
  };

  return (
    <Fragment>
      <Typography variant="h3">Summarize By AI <AutoAwesomeIcon style={{ color: "#FFD700" }}/></Typography>
      <Card className={styles.infoCard}>
        <CardContent className={styles.wrapPondSummary}>
          {!isSummaryGenerated && (
            <div className={styles.generateSummaryButton}>
              <Button
                variant="contained"
                onClick={generateSummary}
                disabled={isButtonDisabled}
              >
                {buttonText}
              </Button>
            </div>
          )}
          {isSummaryGenerated && (
            <>
              <Typography className={styles.markdownContent}>
                {messages.map((message, index) => (
                  <ReactMarkdown key={index} rehypePlugins={[rehypeRaw]}>
                    {message}
                  </ReactMarkdown>
                ))}
              </Typography>

              {/* Regenerate Button */}
              <div className={styles.regenerateSummaryButton}>
                <Button
                  variant="contained"
                  size="small" // Make the button smaller
                  startIcon={<RefreshIcon />} // Add an icon
                  onClick={generateSummary}
                  disabled={isButtonDisabled}
                >
                    Regenerate
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </Fragment>
  );
};
