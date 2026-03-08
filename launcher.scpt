on run
	set scriptPath to "/Users/mikestavrou/Desktop/ANTIGRAVITY/TRADING DASHBOARD MIKE/start_server.sh"
	-- The crucial part: ">/dev/null 2>&1 &" forces AppleScript to completely detach and exit instantly
	do shell script "bash " & quoted form of scriptPath & " >/dev/null 2>&1 &"
end run
