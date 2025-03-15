{
  "Comment": "State machine for automating anime post workflow with MoviePy",
  "StartAt": "FetchRSS",
  "States": {
    "FetchRSS": {
      "Type": "Task",
      "Resource": "${fetch_rss_arn}",
      "ResultPath": "$.rssData",
      "Next": "CheckPost"
    },
    "CheckPost": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.rssData.status",
          "StringEquals": "anime_post_found",
          "Next": "ProcessContent"
        }
      ],
      "Default": "EndWorkflow"
    },
    "ProcessContent": {
      "Type": "Task",
      "Resource": "${process_content_arn}",
      "ResultPath": "$.processedContent",
      "Next": "StoreData"
    },
    "StoreData": {
      "Type": "Task",
      "Resource": "${store_data_arn}",
      "ResultPath": "$.storeResult",
      "Next": "RenderVideo"
    },
    "RenderVideo": {
      "Type": "Task",
      "Resource": "${render_video_arn}",
      "ResultPath": "$.videoResult",
      "Next": "NotifyUser"
    },
    "NotifyUser": {
      "Type": "Task",
      "Resource": "${notify_post_arn}",
      "InputPath": "$.videoResult",
      "ResultPath": "$.notificationResult",
      "End": true
    },
    "EndWorkflow": {
      "Type": "Succeed"
    }
  }
}
