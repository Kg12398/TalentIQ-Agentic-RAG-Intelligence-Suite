# TalentIQ | SaaS HR Intelligence Frontend

This is a production-ready React (Vite) frontend for the TalentIQ Agentic RAG system. It is designed with a modern SaaS aesthetic, featuring professional HR color palettes, smooth animations, and intelligent candidate recognition.

## 🚀 Quick Start Instructions

### 1. Prerequisites
Ensure you have **Node.js (v18+)** installed on your machine.
- [Download Node.js](https://nodejs.org/)

### 2. Installation
Open your terminal (CMD or PowerShell), navigate to this folder, and run:
```bash
cd talentiq-frontend
npm install
```

### 3. Start the Development Server
```bash
npm run dev
```
The app will be available at **http://localhost:3000**.

## 🛠️ Key Architectural Features
- **Modern Stack**: Built with Vite, React 18, and Tailwind CSS.
- **Dynamic Candidate Extraction**: Automatically identifies and lists names from AI responses in the sidebar.
- **Skill Recognition**: High-performance Regex-based highlighting for technical skills (Python, ML, etc.).
- **Premium UX**: Framer Motion powered entry animations and custom-styled sidebar/scrollbars.
- **Backend Ready**: Integrated with Axios and configured to proxy `http://localhost:8000` (FastAPI).

## 📁 Folder Structure
- `/src/components`: UI modules (Sidebar, Chat, MessageBubble).
- `/src/api`: Axios client for backend communication.
- `/src/App.jsx`: Main dashboard layout and state logic.
- `/tailwind.config.js`: Custom HR indigo/slate theme colors.
