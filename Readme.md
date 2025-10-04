## Quick Info For Test Scripts

### 1. API Key is only required for pulling YouTube comments  
Steps to get API key:  
- Go To GCP:  https://console.cloud.google.com/  
- Create or Select a Project  
- Enable YouTube Data API v3 (Search for it and click enable)  
- Create API Credentials:   
Go to "APIs & Services" -> "Credentials  
Click "+ CREATE CREDENTIALS" -> "API key"  
Consider restricting it to YouTube Data API for security  

### 2. Replace ""YOUR_API_KEY_HERE" with your key.
  
### 3. The "_simple" does the same thing, but less functions, and easier to follow.  

**Note: Later, API keys should never be exposed on Github, should have private environment file that we each have.**