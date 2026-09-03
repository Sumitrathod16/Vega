# VEGA

VEGA is a voice-first AI desktop assistant built in Python.

The goal of VEGA is to create a personal AI assistant that can understand natural voice commands, communicate through speech, control desktop functions, search the web, understand the computer screen, and eventually execute multi-step tasks autonomously.

VEGA uses local AI models through Ollama to keep most AI processing on the user's own machine.

## Current Features

- Wake word activation
- Continuous conversation mode
- Voice input
- Voice output
- Voice interruption
- Local AI conversation using Ollama
- Application launching
- Dynamic volume control
- Mute and unmute controls
- Manual web search
- Automatic web-search detection
- Screen awareness
- Screen error analysis
- Code-screen analysis
- Webpage understanding
- Basic UI navigation guidance

## AI Architecture

VEGA currently uses multiple models for different responsibilities.

```text
User Voice
    |
    v
Faster Whisper
    |
    v
Command Router
    |
    +-----------------------------+
    |              |              |
    v              v              v
Local Command    Web Search    AI Conversation
                                  |
                                  v
                            Llama 3.2 3B
```

For screen understanding:

```text
Computer Screen
      |
      v
Screenshot
      |
      v
Moondream
Visual Understanding
      |
      v
Llama 3.2 3B
Reasoning
      |
      v
VEGA Voice Response
```

Moondream acts primarily as VEGA's visual system while Llama handles higher-level reasoning.

## Project Structure

```text
Vega/
|
|-- listener.py
|-- brain.py
|-- speaker.py
|-- apps.py
|-- system_control.py
|-- web_search.py
|-- screen_reader.py
|-- requirement.txt
|-- README.md
|
`-- venv/
```

### listener.py

Handles:

- microphone input
- speech recognition
- wake-word detection
- command routing
- conversation mode
- speech interruption

### brain.py

Handles:

- local AI conversation
- Ollama communication
- reasoning
- web-result reasoning
- automatic web detection

### speaker.py

Handles:

- text-to-speech
- VEGA voice output
- speech interruption
- audio cleanup

### apps.py

Handles desktop application launching.

### system_control.py

Handles system operations such as:

- volume increase
- volume decrease
- exact volume setting
- mute
- unmute
- current volume detection

### web_search.py

Handles dynamic internet searches and provides search information to VEGA's AI brain.

### screen_reader.py

Handles VEGA's screen-awareness system.

Current pipeline:

```text
Screenshot
    |
    v
Vision Model
    |
    v
Screen Context
    |
    v
Reasoning Model
    |
    v
Response
```

## Requirements

Recommended environment:

- Windows 10/11
- Python 3.11 through 3.13 (Python 3.14 is not currently supported by all audio dependencies)
- Microphone
- Internet connection for web features
- Ollama
- At least 8 GB RAM recommended

Install Python dependencies:

```powershell
pip install -r requirement.txt

# Playwright needs its browser binaries installed separately.
playwright install chromium
```

## Ollama Setup

Ollama must be installed separately.

After installing Ollama, download the required models:

```powershell
ollama pull llama3.2:3b
```

```powershell
ollama pull moondream
```

Verify installed models:

```powershell
ollama list
```

Make sure Ollama is running before starting VEGA.

If required:

```powershell
ollama serve
```

## Installation

Clone the repository:

```powershell
git clone <your-repository-url>
```

Enter the project directory:

```powershell
cd Vega
```

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirement.txt
playwright install chromium
```

Make sure the Ollama models are available:

```powershell
ollama list
```

Then start VEGA:

```powershell
python listener.py
```

## Example Commands

Wake VEGA:

```text
Hey Vega
```

General conversation:

```text
Explain machine learning in simple terms.
```

Application control:

```text
Open Chrome.
```

Volume control:

```text
Increase the volume by 5 percent.
```

```text
Set volume to 40 percent.
```

Web search:

```text
Search the web for latest AI news.
```

Screen awareness:

```text
What is on my screen?
```

```text
Explain this error.
```

```text
What is wrong with this code?
```

```text
What should I click?
```

Sleep mode:

```text
Vega, go to sleep.
```

Shutdown:

```text
Shutdown Vega.
```

## Development Roadmap

### Completed / In Development

- [x] Wake word
- [x] AI conversation
- [x] Continuous conversation
- [x] Voice output
- [x] Voice interruption
- [x] Application control
- [x] System volume control
- [x] Web search
- [x] Automatic web detection
- [x] Basic screen awareness
- [x] Screen-based error analysis
- [x] Basic UI guidance
- [ ] Screen context/change awareness

### Planned

- [ ] Long-term memory
- [ ] Conversation memory
- [ ] Task execution / Agent Mode
- [ ] Browser control
- [ ] Mouse and keyboard automation
- [ ] File-system interaction
- [ ] Multi-step task planning
- [ ] Background startup
- [ ] Improved real-time voice recognition
- [ ] Response streaming
- [ ] Mobile companion
- [ ] Shared laptop/mobile memory
- [ ] Multi-device VEGA architecture

## Future Architecture

The long-term goal is for VEGA to operate across multiple personal devices.

```text
                 VEGA Core
                     |
             Shared Memory
                     |
          +----------+----------+
          |                     |
          v                     v
       Laptop                 Mobile
          |                     |
   Screen / Apps          Mic / Camera
   Files / Browser        Notifications
   System Control         Mobile Actions
```

The laptop and mobile versions will eventually share the same VEGA identity and memory.

## Privacy

VEGA is designed with local processing in mind.

Local Ollama models can process AI requests directly on the user's machine.

Future sensitive actions such as:

- deleting files
- sending messages
- installing software
- changing system settings

should require explicit user confirmation before execution.

## Status

VEGA is currently under active development.

The current version is an experimental desktop AI assistant and should not be considered production-ready.

## Author

**Sumit Rathod**

GitHub: `Sumitrathod16`

---

Built as a personal AI assistant project with the goal of creating a fast, intelligent, voice-first desktop companion.