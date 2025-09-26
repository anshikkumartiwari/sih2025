# LM Compliance Checker Chrome Extension

A Chrome extension that instantly checks Legal Metrology compliance for e-commerce products with AI-powered analysis.

## 🚀 Features

- **One-Click Analysis**: Automatically captures current tab URL
- **Real-time Processing**: Instant compliance checking without leaving the page
- **Compact Interface**: Professional popup design matching the main app
- **Multi-Platform Support**: Amazon, Blinkit, and more e-commerce sites
- **Progressive States**: Loading indicators and step-by-step progress
- **Results Summary**: Quick compliance overview with detailed insights

## 📦 Installation

### Development Installation

1. **Ensure Flask Backend is Running**
   ```bash
   cd ../  # Go back to main project directory
   pip install flask-cors  # Install CORS support
   python app.py  # Start Flask server on http://127.0.0.1:5000
   ```

2. **Load Extension in Chrome**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `chrome-extension` folder
   - The extension will appear in your extensions list

3. **Create Icons** (Optional)
   - Open `generate-icons.html` in your browser
   - Download the generated icons as `icon16.png`, `icon48.png`, `icon128.png`
   - Place them in the `icons/` folder

## 🎯 Usage

1. **Navigate to a Product Page**
   - Visit any supported e-commerce site (Amazon, Blinkit)
   - Go to a specific product page

2. **Click Extension Icon**
   - Click the LM Compliance Checker icon in Chrome toolbar
   - The popup will show current page information

3. **Check Compliance**
   - Click "Check Compliance" button
   - Watch real-time progress through crawling, OCR, and validation
   - View instant results in the popup

4. **View Detailed Report**
   - Click "View Full Report" to open complete analysis in web app
   - Use "Check Another" to analyze more products

## 🛠️ Technical Details

### Architecture
- **Frontend**: Chrome Extension with Manifest V3
- **Backend**: Flask REST API with CORS support
- **Communication**: JSON API calls to `http://127.0.0.1:5000/api/analyze`

### File Structure
```
chrome-extension/
├── manifest.json          # Extension configuration
├── popup.html            # Extension popup interface
├── popup.css             # Styling for popup
├── popup.js              # Main extension logic
├── icons/                # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md            # This file
```

### API Endpoints
- `POST /api/analyze` - Analyze product URL
- `GET /api/status` - Check service status

## 🎨 Design Features

### Visual States
- **Initial State**: Shows current page with supported site indicators
- **Loading State**: Animated progress with step indicators
- **Results State**: Compliance score with quick field summary
- **Error State**: User-friendly error handling with retry options

### UI Components
- Professional dark theme matching main app
- Compact 380px width popup optimized for extension use
- Responsive design for different popup heights
- Smooth animations and transitions
- Status indicators for supported/unsupported sites

## 🔧 Configuration

### Supported Sites
Currently supports:
- `amazon.in`
- `amazon.com` 
- `blinkit.com`

To add more sites, update:
1. `SUPPORTED_SITES` array in `popup.js`
2. `host_permissions` in `manifest.json`
3. Backend crawler support in main app

### API Configuration
Default Flask backend: `http://127.0.0.1:5000`

To change the backend URL, update `API_BASE` in `popup.js`

## 📱 Browser Compatibility

- **Chrome**: Full support (Manifest V3)
- **Edge**: Compatible with Chromium-based Edge
- **Firefox**: Requires manifest conversion for Firefox format

## 🚧 Development

### Local Development
1. Make changes to extension files
2. Click "Reload" button in `chrome://extensions/` for the extension
3. Test functionality on supported e-commerce sites

### Debugging
- Right-click extension popup → "Inspect" to open DevTools
- Check console for error messages
- Use Network tab to monitor API calls

## 📝 Version History

### v1.0.0
- Initial release
- Basic compliance checking
- Support for Amazon and Blinkit
- Professional popup interface
- Real-time progress indicators

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes to extension files
4. Test thoroughly on supported sites
5. Submit pull request

## 📄 License

This extension is part of the SIH2025 Legal Metrology Compliance Checker project.

## 🆘 Support

For issues or questions:
1. Check Flask backend is running on port 5000
2. Verify site is in supported sites list
3. Check extension permissions are granted
4. Review browser console for error messages

---

**Made with ❤️ for Legal Metrology Compliance**