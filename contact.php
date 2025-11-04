<?php
/* -----------------------------------------
   Simple contact/subscribe handler for PHP
   - Uses PHP mail() by default
   - Optional: switch to PHPMailer SMTP (recommended)
   ----------------------------------------- */

/////////////////////////////////////////////
// 1) BASIC SETTINGS — CHANGE THESE
/////////////////////////////////////////////
$toEmail   = 'you@yourdomain.com';     // where messages should arrive
$fromEmail = 'no-reply@yourdomain.com';// envelope From (same domain to pass SPF)
$siteName  = 'samcheeseman.com';

/////////////////////////////////////////////
// 2) QUICK SPAM TRAP (honeypot)
/////////////////////////////////////////////
if (!empty($_POST['_honey'])) {
  http_response_code(204); // silently ignore bots
  exit;
}

/////////////////////////////////////////////
// 3) NORMALIZE + VALIDATE INPUT
/////////////////////////////////////////////
$formType = isset($_POST['form']) ? strtolower(trim($_POST['form'])) : 'contact';

$name    = trim($_POST['name']    ?? '');
$email   = trim($_POST['email']   ?? '');
$subject = trim($_POST['subject'] ?? '');
$message = trim($_POST['message'] ?? '');

$ip      = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$agent   = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
$referer = $_SERVER['HTTP_REFERER'] ?? 'unknown';

if ($formType === 'subscribe') {
  if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo 'Invalid email';
    exit;
  }
  $subjectLine = "New subscribe: {$email}";
  $body = "A new user subscribed on {$siteName}\n\nEmail: {$email}\nIP: {$ip}\nRef: {$referer}\nUA: {$agent}\n";
} else {
  if (!$name || !filter_var($email, FILTER_VALIDATE_EMAIL) || !$message) {
    http_response_code(400);
    echo 'Missing required fields';
    exit;
  }
  $subjectLine = $subject ? $subject : 'New contact form submission';
  $body =
    "New message from {$siteName}\n\n".
    "Name: {$name}\n".
    "Email: {$email}\n".
    ($subject ? "Subject: {$subject}\n" : '').
    "Message:\n{$message}\n\n".
    "IP: {$ip}\nRef: {$referer}\nUA: {$agent}\n";
}

/////////////////////////////////////////////
// 4) SEND VIA PHP mail()  (fastest to start)
/////////////////////////////////////////////
$headers  = "From: {$siteName} <{$fromEmail}>\r\n";
$headers .= "Reply-To: {$email}\r\n";
$headers .= "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

$ok = @mail($toEmail, $subjectLine, $body, $headers);

if ($ok) {
  // Redirect back with a thank-you (optional)
  $next = !empty($_POST['_next']) ? $_POST['_next'] : '/thank-you.html';
  header("Location: {$next}");
  exit;
}

// Fallback error
http_response_code(500);
echo 'Sorry, your message could not be sent. Please try again later.';