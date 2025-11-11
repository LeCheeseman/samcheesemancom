<?php
/* -----------------------------------------
   Simple contact/subscribe handler for PHP
   - Uses PHP mail() by default
   - Optional: switch to PHPMailer SMTP (recommended)
   ----------------------------------------- */

/////////////////////////////////////////////
// 1) BASIC SETTINGS — CHANGE THESE
/////////////////////////////////////////////
$toEmail   = 'sam@samcheeseman.com';        // where messages should arrive
$siteName  = 'samcheeseman.com';

// Gmail / Google Workspace SMTP (requires 2‑step verification + App Password)
//  - Set $smtpUser to your full Gmail/Workspace address
//  - Create an App Password in your Google Account (Security → App passwords)
//  - Paste it into $smtpPass
$smtpHost  = 'smtp.gmail.com';
$smtpUser  = 'sam@samcheeseman.com';
$smtpPass  = 'emqpoyvbszpmthae';
$smtpPort  = 465; // 465 (smtps) or 587 (starttls)
$smtpSecure= 'ssl'; // 'ssl' for 465, 'tls' for 587

// Try to load PHPMailer via Composer; falls back to mail() if unavailable
if (file_exists(__DIR__ . '/vendor/autoload.php')) {
  require __DIR__ . '/vendor/autoload.php';
}
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

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
  $subjectLine = "[Website Subscribe] {$siteName}";
  $bodyText =
    "New subscribe on {$siteName}\n\n" .
    "Email: {$email}\n" .
    "IP: {$ip}\n" .
    "Ref: {$referer}\n" .
    "UA: {$agent}\n";
  $bodyHtml =
    "<!doctype html><html><body style=\"font:14px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#111;margin:0;padding:24px;background:#f7f7f7;\">" .
    "<table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"max-width:640px;margin:0 auto;background:#fff;border:1px solid #eee;border-radius:8px;overflow:hidden;\">" .
    "<tr><td style=\"padding:16px 20px;background:#111;color:#fff;font-weight:600\">New Subscribe</td></tr>" .
    "<tr><td style=\"padding:20px\">" .
    "<table role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\" style=\"width:100%\">" .
    "<tr><td style=\"padding:8px 0;width:140px;color:#666\">Site</td><td style=\"padding:8px 0\">{$siteName}</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">Email</td><td style=\"padding:8px 0\">".htmlspecialchars($email, ENT_QUOTES, 'UTF-8')."</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">IP</td><td style=\"padding:8px 0\">{$ip}</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">Referrer</td><td style=\"padding:8px 0\">".htmlspecialchars($referer, ENT_QUOTES, 'UTF-8')."</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">User-Agent</td><td style=\"padding:8px 0\">".htmlspecialchars($agent, ENT_QUOTES, 'UTF-8')."</td></tr>" .
    "</table></td></tr></table></body></html>";
} else {
  if (!$name || !filter_var($email, FILTER_VALIDATE_EMAIL) || !$message) {
    http_response_code(400);
    echo 'Missing required fields';
    exit;
  }
  $subjectLine = "[Website Contact] {$siteName}" . ($subject ? " — {$subject}" : "");
  $bodyText =
    "New message from {$siteName}\n\n" .
    "Name: {$name}\n" .
    "Email: {$email}\n" .
    ($subject ? "Subject: {$subject}\n" : "") .
    "Message:\n{$message}\n\n" .
    "IP: {$ip}\nRef: {$referer}\nUA: {$agent}\n";
  $bodyHtml =
    "<!doctype html><html><body style=\"font:14px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#111;margin:0;padding:24px;background:#f7f7f7;\">" .
    "<table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"max-width:640px;margin:0 auto;background:#fff;border:1px solid #eee;border-radius:8px;overflow:hidden;\">" .
    "<tr><td style=\"padding:16px 20px;background:#111;color:#fff;font-weight:600\">New Contact Message</td></tr>" .
    "<tr><td style=\"padding:20px\">" .
    "<table role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\" style=\"width:100%\">" .
    "<tr><td style=\"padding:8px 0;width:140px;color:#666\">Site</td><td style=\"padding:8px 0\">{$siteName}</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">Name</td><td style=\"padding:8px 0\">".htmlspecialchars($name, ENT_QUOTES, 'UTF-8')."</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">Email</td><td style=\"padding:8px 0\">".htmlspecialchars($email, ENT_QUOTES, 'UTF-8')."</td></tr>" .
    ($subject ? "<tr><td style=\"padding:8px 0;color:#666\">Subject</td><td style=\"padding:8px 0\">".htmlspecialchars($subject, ENT_QUOTES, 'UTF-8')."</td></tr>" : "") .
    "<tr><td style=\"padding:8px 0;color:#666;vertical-align:top\">Message</td><td style=\"padding:8px 0;white-space:pre-wrap\">".nl2br(htmlspecialchars($message, ENT_QUOTES, 'UTF-8'))."</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">IP</td><td style=\"padding:8px 0\">{$ip}</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">Referrer</td><td style=\"padding:8px 0\">".htmlspecialchars($referer, ENT_QUOTES, 'UTF-8')."</td></tr>" .
    "<tr><td style=\"padding:8px 0;color:#666\">User-Agent</td><td style=\"padding:8px 0\">".htmlspecialchars($agent, ENT_QUOTES, 'UTF-8')."</td></tr>" .
    "</table></td></tr></table></body></html>";
}

/////////////////////////////////////////////
// 4) SEND — Prefer Gmail SMTP via PHPMailer; fallback to mail()
/////////////////////////////////////////////
$sent = false;
$debugLog  = __DIR__ . '/mail.log';
$debugMsgs = [];

if (class_exists('PHPMailer\\PHPMailer\\PHPMailer') && !empty($smtpUser) && !empty($smtpPass)) {
  // Try SSL:465 first, then TLS:587
  $attempts = [
    ['secure' => 'ssl', 'port' => 465],
    ['secure' => 'tls', 'port' => 587],
  ];

  foreach ($attempts as $i => $cfg) {
    if ($sent) break;
    try {
      $mailer = new PHPMailer(true);
      $mailer->CharSet = 'UTF-8';
      $mailer->isSMTP();
      $mailer->Host       = $smtpHost;
      $mailer->SMTPAuth   = true;
      $mailer->Username   = $smtpUser;           // full Gmail/Workspace address
      $mailer->Password   = $smtpPass;           // Google App Password

      if ($cfg['secure'] === 'ssl') {
        $mailer->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
      } else {
        $mailer->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
      }
      $mailer->Port       = (int)$cfg['port'];

      // From/To (Gmail requires From = authenticated user or verified alias)
      $mailer->setFrom($smtpUser, $siteName);
      $mailer->addAddress($toEmail);
      if (!empty($email)) {
        $mailer->addReplyTo($email, $name ?: $email);
      }

      // Content
      $mailer->Subject = $subjectLine;
      $mailer->isHTML(true);
      $mailer->Body    = $bodyHtml;
      $mailer->AltBody = $bodyText;

      $sent = $mailer->send();
      if (!$sent) {
        $debugMsgs[] = 'Attempt '.($i+1).' failed without exception: ' . ($mailer->ErrorInfo ?: 'unknown error');
      }
    } catch (Exception $e) {
      $debugMsgs[] = 'Attempt '.($i+1).' exception: '.$e->getMessage();
      $sent = false;
    }
  }
}

if (!$sent) {
  // Fallback: PHP mail() — less reliable but keeps things working
  $fromEmail = $smtpUser ?: ('no-reply@' . parse_url('https://' . $_SERVER['HTTP_HOST'], PHP_URL_HOST));
  $headers  = "From: {$siteName} <{$fromEmail}>\r\n";
  if (!empty($email)) {
    $headers .= "Reply-To: {$email}\r\n";
  }
  $headers .= "MIME-Version: 1.0\r\n";
  $headers .= "Content-Type: text/html; charset=UTF-8\r\n";
  $sent = @mail($toEmail, $subjectLine, $bodyHtml, $headers);
  if (!$sent) {
    $debugMsgs[] = 'mail() fallback reported failure';
  }
}

if ($sent) {
  $next = !empty($_POST['_next']) ? $_POST['_next'] : '/contact.html?sent=1';
  header("Location: {$next}");
  exit;
}

// Log debug info if any SMTP attempts failed
if (!empty($debugMsgs)) {
  $log = date('c') . " " . ($_SERVER['REMOTE_ADDR'] ?? '-') . " " . ($_SERVER['HTTP_USER_AGENT'] ?? '-') . "\n"
       . implode("\n", $debugMsgs) . "\n" . str_repeat('-', 40) . "\n";
  @file_put_contents($debugLog, $log, FILE_APPEND);
}

http_response_code(500);
echo 'Sorry, your message could not be sent. Please try again later.';