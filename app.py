"""
FarmDirect - Application Launcher
Convenience wrapper that exports and runs the Flask app from server.py.
You can run either:
    python server.py
or:
    python app.py
"""

from server import app

if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=================================================================")
    print(" [*] FarmDirect - Farmer-to-Customer Marketplace Server Started")
    print(" Access the website at: http://127.0.0.1:5000")
    print("=================================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
