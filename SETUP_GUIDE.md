# 🚀 Innov8 Adaptive Coding Interview Platform - Setup Guide

## 📋 Overview
The system is now complete with all requested features:
- ✅ Backend server with adaptive question generation
- ✅ Code execution with time/space complexity analysis  
- ✅ Gemini AI professional interviewer
- ✅ Adaptive problem selection from knowledge base
- ✅ Simplified frontend with SUBMIT button
- ✅ Chat system that guides without revealing answers

## 🔧 Configuration Setup

### 1. Backend Configuration

#### Required Environment Variables
Create a `.env` file in the `backend` directory:

```env
# Gemini AI API Key (Required for AI interviewer)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Backend Port (defaults to 8000)
PORT=8000
```

#### Get Gemini API Key:
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key
5. Copy the key and paste it in the `.env` file

### 2. Install Dependencies

#### Backend Dependencies:
```bash
cd "d:\Innov8 Final Round\backend"
pip install -r requirements.txt
```

#### Frontend Dependencies:
```bash
cd "d:\Innov8 Final Round\frontend"  
npm install
```

### 3. Verify Knowledge Base
Ensure these files exist:
- `knowledge_base/data_json.json` (Graph structure with problems)
- `knowledge_base/ques_data.json` (Flat question format)

## 🚀 Running the System

### Start Backend Server:
```bash
cd "d:\Innov8 Final Round\backend"
python server.py
```
The server will start on http://localhost:8000

### Start Frontend:
```bash
cd "d:\Innov8 Final Round\frontend"
npm run dev
```
The frontend will start on http://localhost:3000

## 🎯 How to Use - Coding Interview Flow

### 1. **Start Interview**
- Open http://localhost:3000
- The system loads an adaptive question from the knowledge base
- Timer starts automatically based on difficulty level

### 2. **Code and Get Guidance**
- Write your solution in the editor
- Use **▶ Run** button to test your code
- The AI interviewer provides hints every 10 seconds if needed
- Chat with the interviewer for guidance (it won't reveal answers)

### 3. **Submit Solution**
- Click **✓ Submit** when ready
- System analyzes your solution for:
  - Correctness
  - Time complexity (O(n), O(1), etc.)
  - Space complexity  
  - Code quality
- Gets performance score (0-100)

### 4. **Adaptive Question Generation**
- Based on your performance, system selects next question:
  - Score ≥80: Increase difficulty
  - Score 60-79: Maintain/slight increase  
  - Score <60: Decrease difficulty
- Avoids recently asked questions
- Filters by topics if needed

### 5. **End Interview**
- Type "END" in chat to finish
- System provides final assessment with statistics

## 🤖 AI Interviewer Features

### Professional Guidance:
- **Hints**: When you ask "help" or say you're "stuck"
- **Nudges**: When code has errors or issues
- **Encouragement**: For substantial code progress
- **Warnings**: For potential mistakes

### Chat Commands:
- Normal conversation for guidance
- "END" - Finish interview and get assessment
- AI monitors your progress and provides proactive help

## 📊 Features Overview

### Backend Endpoints:
- `GET /api/adaptive/question` - Get adaptive question
- `POST /api/execute` - Execute code with complexity analysis
- `POST /api/submit` - Submit solution and get next question
- `POST /api/chat` - Chat with AI interviewer

### Frontend Components:
- **Adaptive Problem Panel**: Shows current challenge with timer
- **Code Editor**: Monaco editor with syntax highlighting
- **Submit Button**: Green submit button for solution evaluation
- **Chat Panel**: AI interviewer communication
- **Console**: Execution output and complexity analysis

### Complexity Analysis:
- Measures execution time for different input sizes (10, 100, 500, 1000, 5000)
- Calculates time complexity patterns (O(1), O(n), O(n²), etc.)
- Monitors memory usage for space complexity
- Provides detailed analysis and recommendations

## 🎓 Interview Best Practices

### For Candidates:
1. Read the problem carefully
2. Ask clarifying questions to the AI interviewer
3. Think out loud while coding
4. Test with different input sizes
5. Optimize if needed before submitting

### AI Interviewer Behavior:
- Never reveals complete solutions
- Provides increasingly specific hints if stuck
- Asks probing questions about approach
- Guides toward optimal solutions
- Maintains professional but encouraging tone

## 🔍 Troubleshooting

### Common Issues:

1. **"AI interviewer not available"**
   - Check GEMINI_API_KEY in `.env` file
   - Verify API key is valid

2. **"Knowledge base not loaded"**
   - Ensure `knowledge_base/ques_data.json` exists
   - Check file path in `server.py`

3. **Code execution timeout**
   - Optimize your algorithm
   - Check for infinite loops
   - Reduce input size for testing

4. **Backend connection failed**
   - Verify backend is running on port 8000
   - Check console for server errors

## 📈 Performance Scoring

### Score Calculation (0-100):
- **40 points**: Successful execution
- **20-40 points**: Time complexity efficiency
- **10 points**: Code conciseness
- **0-20 points**: Hint usage bonus

### Difficulty Progression:
- **Easy → Medium**: Score ≥ 80
- **Medium → Hard**: Score ≥ 80
- **Any → Easier**: Score < 60

## 🎉 Ready to Test!

Your adaptive coding interview platform is now fully configured and ready to use. The system will:

1. ✅ Generate adaptive questions from your knowledge base
2. ✅ Execute code with time/space complexity analysis
3. ✅ Provide professional AI interviewer guidance
4. ✅ Adapt difficulty based on performance
5. ✅ Track session statistics and progress

Start the servers and navigate to http://localhost:3000 to begin your first AI-powered coding interview!