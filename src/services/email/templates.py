"""Email templates for various notification types."""


class EmailTemplate:
    """HTML email templates."""

    @staticmethod
    def license_activation_template(
        customer_name: str,
        license_name: str,
        license_key: str,
        license_seats: int,
        company_name: str,
    ) -> str:
        """Generate license activation email HTML."""
        # ruff: noqa: E501
        return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html dir="ltr" lang="en">
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />
    <meta name="x-apple-disable-message-reformatting" />
</head>
<body style="background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen-Sans,Ubuntu,Cantarell,'Helvetica Neue',sans-serif">
    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation">
        <tbody>
            <tr>
                <td style="background-color:#f6f9fc">
                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="max-width:37.5em;margin:30px auto;background-color:#fff;border-radius:8px;overflow:hidden">
                        <tbody>
                            <tr style="width:100%">
                                <td>
                                    <!-- Header -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f8f9fa;padding:20px 40px;border-bottom:1px solid #e5e7eb">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <h1 style="font-size:20px;font-weight:600;color:#1f2937;margin:0">{company_name}</h1>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Main Content -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:0 40px">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <hr style="width:100%;border:none;border-top:1px solid #e8eaed;margin:20px 0" />
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:20px 0">Dear {customer_name},</p>
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:16px 0">Great news! Your payment has been successfully processed and your license is now <b>active</b>.</p>
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:16px 0">You can now use your license key to activate your software and start using all the features included in your plan.</p>
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:16px 0">If you need any assistance with activation or have questions, our support team is here to help.</p>
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:20px 0 8px 0">Best regards,</p>
                                                    <p style="font-size:16px;line-height:24px;color:#3c4043;margin:0 0 20px 0;font-weight:600">The {company_name} Team</p>
                                                    <hr style="width:100%;border:none;border-top:1px solid #e8eaed;margin:20px 0" />
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- License Details -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:0 40px;margin-top:8px">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:#f8f9fa;border-radius:8px;padding:24px">
                                                        <tbody>
                                                            <tr>
                                                                <td>
                                                                    <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                                                        <tr>
                                                                            <td style="padding:8px 0">
                                                                                <span style="font-size:13px;color:#5f6368;text-transform:uppercase;letter-spacing:0.5px">License Name</span>
                                                                            </td>
                                                                            <td align="right" style="padding:8px 0">
                                                                                <span style="font-size:14px;color:#202124;font-weight:600">{license_name}</span>
                                                                            </td>
                                                                        </tr>
                                                                        <tr>
                                                                            <td style="padding:8px 0">
                                                                                <span style="font-size:13px;color:#5f6368;text-transform:uppercase;letter-spacing:0.5px">Seats</span>
                                                                            </td>
                                                                            <td align="right" style="padding:8px 0">
                                                                                <span style="font-size:14px;color:#202124;font-weight:600">{license_seats}</span>
                                                                            </td>
                                                                        </tr>
                                                                        <tr>
                                                                            <td colspan="2" style="padding:16px 0 8px 0;border-top:1px solid #dadce0">
                                                                                <p style="font-size:13px;color:#5f6368;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 8px 0">License Key</p>
                                                                                <p style="font-size:16px;color:#1f2937;font-weight:700;margin:0;font-family:monospace;background-color:#fff;padding:12px;border-radius:4px;border:1px solid #e5e7eb">{license_key}</p>
                                                                            </td>
                                                                        </tr>
                                                                    </table>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Support Section -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f9fafb;margin:32px 0;padding:24px 40px">
                                        <tbody>
                                            <tr>
                                                <td align="center">
                                                    <p style="font-size:14px;line-height:22px;color:#3c4043;margin:0">Need help with activation?</p>
                                                    <p style="font-size:14px;line-height:22px;margin:8px 0 0 0"><a href="mailto:contact@vohrad.be" style="color:#2563eb;text-decoration:underline;font-weight:600">contact@vohrad.be</a></p>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Footer -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:24px 40px;background-color:#fafafa">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <p style="font-size:12px;line-height:20px;color:#5f6368;text-align:center;margin:0">© 2025 {company_name}. All rights reserved.</p>
                                                    <p style="font-size:12px;line-height:20px;color:#5f6368;text-align:center;margin:8px 0 0 0">This is an automated activation notification. Please do not reply to this email.</p>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</body>
</html>"""

    @staticmethod
    def invoice_template(
        customer_name: str,
        invoice_url: str,
        amount: str,
        currency: str,
        due_date: str,
        invoice_number: str,
        company_name: str,
        invoice_pdf_url: str = "",
        license_name: str = "",
        license_seats: int = 0,
    ) -> str:
        """Generate invoice email HTML."""
        # ruff: noqa: E501
        pdf_link = f'<a href="{invoice_pdf_url or invoice_url}" style="color: #2563eb; text-decoration: underline; font-size: 14px;">Download PDF</a>' if invoice_pdf_url else ''
        return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html dir="ltr" lang="en">
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />
    <meta name="x-apple-disable-message-reformatting" />
</head>
<body style="background-color:#f6f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen-Sans,Ubuntu,Cantarell,'Helvetica Neue',sans-serif">
    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation">
        <tbody>
            <tr>
                <td style="background-color:#f6f9fc">
                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="max-width:37.5em;margin:30px auto;background-color:#fff;border-radius:8px;overflow:hidden">
                        <tbody>
                            <tr style="width:100%">
                                <td>
                                    <!-- Header -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f8f9fa;padding:20px 40px;border-bottom:1px solid #e5e7eb">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <h1 style="font-size:20px;font-weight:600;color:#1f2937;margin:0">{company_name}</h1>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Main Content -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:0 40px">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <hr style="width:100%;border:none;border-top:1px solid #e8eaed;margin:20px 0" />
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:20px 0">Dear {customer_name},</p>
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:16px 0">Thank you for your business with {company_name}. We appreciate your trust in our services.</p>
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:16px 0">This invoice is for your <b>{license_name}</b> license with <b>{license_seats} seats</b>. Please review the details below and proceed with payment at your earliest convenience.</p>
                                                    <p style="font-size:14px;line-height:24px;color:#3c4043;margin:16px 0">Your license will be automatically activated immediately upon successful payment. You will receive a confirmation email with your license key and activation instructions.</p>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Invoice Details -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:0 40px;margin-top:24px">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:#f8f9fa;border-radius:8px;padding:24px">
                                                        <tbody>
                                                            <tr>
                                                                <td>
                                                                    <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                                                        <tr>
                                                                            <td style="padding:8px 0">
                                                                                <span style="font-size:13px;color:#5f6368;text-transform:uppercase;letter-spacing:0.5px">Invoice Number</span>
                                                                            </td>
                                                                            <td align="right" style="padding:8px 0">
                                                                                <span style="font-size:14px;color:#202124;font-weight:600">{invoice_number}</span>
                                                                            </td>
                                                                        </tr>
                                                                        <tr>
                                                                            <td style="padding:8px 0">
                                                                                <span style="font-size:13px;color:#5f6368;text-transform:uppercase;letter-spacing:0.5px">Due Date</span>
                                                                            </td>
                                                                            <td align="right" style="padding:8px 0">
                                                                                <span style="font-size:14px;color:#202124;font-weight:600">{due_date}</span>
                                                                            </td>
                                                                        </tr>
                                                                        <tr>
                                                                            <td style="padding:8px 0">
                                                                                <span style="font-size:13px;color:#5f6368;text-transform:uppercase;letter-spacing:0.5px">License</span>
                                                                            </td>
                                                                            <td align="right" style="padding:8px 0">
                                                                                <span style="font-size:14px;color:#202124;font-weight:600">{license_name} ({license_seats} seats)</span>
                                                                            </td>
                                                                        </tr>
                                                                        <tr>
                                                                            <td style="padding:16px 0 8px 0;border-top:1px solid #dadce0">
                                                                                <span style="font-size:16px;color:#202124;font-weight:700">Total Amount Due</span>
                                                                            </td>
                                                                            <td align="right" style="padding:16px 0 8px 0;border-top:1px solid #dadce0">
                                                                                <span style="font-size:24px;color:#1f2937;font-weight:700">{amount} {currency}</span>
                                                                            </td>
                                                                        </tr>
                                                                    </table>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Payment Button -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:32px 40px">
                                        <tbody>
                                            <tr>
                                                <td align="center">
                                                    <a href="{invoice_url}" style="display:inline-block;padding:14px 48px;background-color:#1f2937;color:#ffffff;text-decoration:none;border-radius:4px;font-size:15px;font-weight:600">Pay Invoice</a>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:0 40px">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <hr style="width:100%;border:none;border-top:1px solid #e8eaed;margin:20px 0" />
                                                    <p style="font-size:14px;line-height:22px;color:#3c4043;margin:16px 0">If you have any questions or need assistance, our support team is here to help.</p>
                                                    <p style="font-size:14px;line-height:22px;color:#3c4043;margin:16px 0">Thank you for choosing {company_name}.</p>
                                                    <p style="font-size:14px;line-height:22px;color:#3c4043;margin:20px 0 8px 0">Best regards,</p>
                                                    <p style="font-size:16px;line-height:22px;color:#3c4043;margin:0;font-weight:600">The {company_name} Team</p>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Support Section -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f9fafb;margin:32px 0;padding:24px 40px">
                                        <tbody>
                                            <tr>
                                                <td align="center">
                                                    <p style="font-size:14px;line-height:22px;color:#3c4043;margin:0">Need assistance? {pdf_link}</p>
                                                    <p style="font-size:14px;line-height:22px;margin:8px 0 0 0"><a href="mailto:contact@vohrad.be" style="color:#2563eb;text-decoration:underline;font-weight:600">contact@vohrad.be</a></p>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>

                                    <!-- Footer -->
                                    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="padding:24px 40px;background-color:#fafafa">
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <p style="font-size:12px;line-height:20px;color:#5f6368;text-align:center;margin:0">© 2025 {company_name}. All rights reserved.</p>
                                                    <p style="font-size:12px;line-height:20px;color:#5f6368;text-align:center;margin:8px 0 0 0">This is an automated invoice notification. Please do not reply to this email.</p>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</body>
</html>"""
