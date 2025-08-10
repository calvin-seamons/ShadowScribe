#!/usr/bin/env node

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Determine the correct Python executable path
const isWindows = process.platform === 'win32';
const venvDir = path.join(__dirname, '..', '.venv');
const pythonPath = isWindows 
  ? path.join(venvDir, 'Scripts', 'python.exe')
  : path.join(venvDir, 'bin', 'python');

// Check if virtual environment Python exists
if (!fs.existsSync(pythonPath)) {
  console.error('Virtual environment Python not found at:', pythonPath);
  console.error('Please ensure the virtual environment is set up correctly.');
  process.exit(1);
}

// Start the backend server
const webAppDir = path.join(__dirname, '..', 'web_app');
const pythonProcess = spawn(pythonPath, ['main.py'], {
  cwd: webAppDir,
  stdio: 'inherit'
});

pythonProcess.on('close', (code) => {
  console.log(`Backend process exited with code ${code}`);
  process.exit(code);
});

pythonProcess.on('error', (err) => {
  console.error('Failed to start backend:', err);
  process.exit(1);
});
