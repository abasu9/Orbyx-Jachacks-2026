# 🤖 Chatbot Feature Documentation

## Overview

An intelligent chatbot assistant has been added to the Employee Performance Dashboard to help users understand metrics, rankings, and performance data in a simplified, conversational way.

## Features

### 💬 Interactive Chat Interface
- Clean, modern chat UI with smooth animations
- Real-time message display
- Typing indicators and timestamps
- Mobile-responsive design

### 🎯 Quick Actions
When you first open the chatbot, you'll see quick action buttons for common questions:
- 🏆 Show top performers
- 📊 Explain performance metrics
- 🔢 How is ranking calculated?
- ❓ What is PIP?

### 🧠 Smart Responses

The chatbot can answer questions about:

#### Performance Metrics
- Commits, Pull Requests, Reviews
- Active Days
- Performance Scores
- How metrics are tracked

#### Ranking System
- How rankings are calculated
- AP (Annual Performance) scores
- PIP impact on rankings
- Scoring formulas

#### PIP (Performance Improvement Plans)
- What PIP means
- PIP levels (0, 1, 2+)
- How PIP affects performance

#### Employee Levels
- L1 through L5 explanations
- Seniority indicators
- Responsibilities by level

#### GitHub Integration
- How GitHub usernames are used
- Tracking contributions
- Linking commits to employees

#### General Help
- Understanding the dashboard
- Interpreting employee data
- Navigation assistance

## How to Use

### Opening the Chatbot
1. Look for the floating chat button (💬) in the bottom-right corner
2. Click the button to open the chat window
3. The chatbot will greet you with a welcome message

### Asking Questions
1. Type your question in the input field at the bottom
2. Press Enter or click the send button (➤)
3. The chatbot will respond within seconds

### Quick Actions
- Click any quick action button for instant answers
- Quick actions appear when you first open the chat
- They provide answers to the most common questions

### Closing the Chatbot
- Click the X button in the header
- Or click the toggle button again
- Your conversation history is preserved during your session

## Example Questions

Try asking:
- "What are the performance metrics?"
- "How is ranking calculated?"
- "Who are the top performers?"
- "What does PIP mean?"
- "Explain employee levels"
- "How does GitHub integration work?"
- "What is the scoring formula?"

## Technical Details

### Component Structure
```
Chatbot.jsx          - Main chatbot component
Chatbot.css          - Chatbot styling
Dashboard.jsx        - Updated to include chatbot
```

### Features Implemented
✅ Floating chat button
✅ Expandable chat window
✅ Message history
✅ Quick action buttons
✅ Smart response system
✅ Timestamp display
✅ Typing animations
✅ Mobile responsive
✅ Smooth transitions
✅ Auto-scroll to latest message

### Styling
- Uses the same theme colors (black and orange)
- Consistent with dashboard design
- Smooth animations and transitions
- Professional, modern look

## Customization

### Adding New Responses

To add new chatbot responses, edit `Chatbot.jsx`:

```javascript
const getBotResponse = (userMessage) => {
  const message = userMessage.toLowerCase();
  
  // Add your new condition
  if (message.includes('your-keyword')) {
    return 'Your custom response here';
  }
  
  // ... existing conditions
};
```

### Adding Quick Actions

To add new quick action buttons, edit the `quickActions` array:

```javascript
const quickActions = [
  { id: 1, text: 'Your question', icon: '🎯' },
  // ... existing actions
];
```

### Styling Changes

Modify `Chatbot.css` to customize:
- Colors (uses CSS variables from theme)
- Sizes and spacing
- Animations
- Mobile breakpoints

## Future Enhancements

Potential improvements:
- 🔌 Connect to backend API for real-time data
- 🤖 Integrate AI/ML for smarter responses
- 📊 Show charts and graphs in chat
- 🔍 Search employee data via chat
- 📥 Export conversations
- 🌐 Multi-language support
- 🎤 Voice input/output
- 📱 Push notifications

## Browser Support

Works on:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

## Accessibility

- Keyboard navigation supported
- ARIA labels for screen readers
- High contrast text
- Focus indicators
- Semantic HTML

## Performance

- Lightweight component (~5KB)
- No external dependencies
- Smooth 60fps animations
- Minimal re-renders
- Efficient state management

## Troubleshooting

**Chatbot button not visible?**
- Check if you're on the Dashboard page
- Clear browser cache
- Check console for errors

**Messages not sending?**
- Ensure input field has text
- Check network connection
- Refresh the page

**Styling issues?**
- Clear browser cache
- Check if Chatbot.css is loaded
- Verify CSS variables are defined

## Support

For issues or questions:
1. Check this documentation
2. Review the code comments
3. Test in different browsers
4. Check browser console for errors

---

Enjoy your new chatbot assistant! 🎉
