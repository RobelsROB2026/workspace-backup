const { execSync } = require('child_process');
try {
  const result = execSync(`osascript -e 'tell application "Google Chrome" to execute front window'\\''s active tab javascript "1+1"'`);
  console.log(result.toString());
} catch(e) {
  console.log("Error:", e.message);
}
