"""
app/services/email_service.py
Servicio para envío de correos usando Gmail SMTP.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def enviar_correo_recuperacion(email_destino: str, token: str, username: str) -> bool:
    """
    Envía el correo de recuperación de contraseña con el token.
    Retorna True si se envió correctamente, False si hubo error.
    """
    enlace = f"https://mentor11-production.up.railway.app/resetear_password.html?token={token}"

    html = f"""
    <div style="font-family: Inter, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #F97316; font-size: 1.8rem; margin: 0;">Mentor 11</h1>
            <p style="color: #64748B; margin-top: 4px;">Plataforma ICFES Saber 11</p>
        </div>
        <h2 style="color: #0F172A; font-size: 1.2rem;">Hola, {username} 👋</h2>
        <p style="color: #334155; line-height: 1.6;">
            Recibimos una solicitud para restablecer la contraseña de tu cuenta.
            Si no fuiste tú, puedes ignorar este correo.
        </p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="{enlace}" style="background: #F97316; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 1rem;">
                Restablecer contraseña
            </a>
        </div>
        <p style="color: #94A3B8; font-size: 0.85rem; text-align: center;">
            Este enlace expira en <strong>30 minutos</strong>.
        </p>
        <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 24px 0;" />
        <p style="color: #94A3B8; font-size: 0.75rem; text-align: center;">
            Si el botón no funciona, copia y pega este enlace en tu navegador:<br/>
            <span style="color: #F97316;">{enlace}</span>
        </p>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Mentor 11 — Restablece tu contraseña"
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = email_destino

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.GMAIL_USER, settings.GMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, email_destino, msg.as_string())

        return True

    except Exception as e:
        print(f"[Email] Error al enviar correo: {e}")
        return False
