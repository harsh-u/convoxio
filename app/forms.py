from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileAllowed

class RegisterForm(FlaskForm):
    business_name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=200)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('WhatsApp Business Number', validators=[DataRequired(), Length(min=10, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create Account')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    pan_file = FileField('Upload PAN', validators=[FileAllowed(['pdf', 'jpg', 'png'], 'PDF, JPG, PNG only!')])
    gst_file = FileField('Upload GST', validators=[FileAllowed(['pdf', 'jpg', 'png'], 'PDF, JPG, PNG only!')])
    submit = SubmitField('Upload')

class WhatsAppMessageForm(FlaskForm):
    recipient = StringField('Phone Number (with country code)', validators=[DataRequired()])
    template = SelectField('Template', choices=[], validators=[DataRequired()])
    language = StringField('Language Code', default='en_US')  # Not shown in UI, set by template
    submit = SubmitField('Send Message')

class BulkMessageForm(FlaskForm):
    template = SelectField('Template', choices=[], validators=[DataRequired()])
    recipients_text = TextAreaField('Phone Numbers', validators=[DataRequired()], 
                                   render_kw={"placeholder": "Enter phone numbers (one per line)\n919876543210\n919876543211\n919876543212"})
    csv_file = FileField('Or Upload CSV File', validators=[FileAllowed(['csv'], 'CSV files only!')])
    submit = SubmitField('Send to All')

class ScheduleMessageForm(FlaskForm):
    recipient = StringField('Phone Number (with country code)', validators=[DataRequired()])
    template = SelectField('Template', choices=[], validators=[DataRequired()])
    scheduled_date = StringField('Date', validators=[DataRequired()], render_kw={"type": "date"})
    scheduled_time = StringField('Time', validators=[DataRequired()], render_kw={"type": "time"})
    submit = SubmitField('Schedule Message')

class TemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired()])
    language = StringField('Language Code', validators=[DataRequired()], default='en_US')
    category = SelectField('Category', choices=[('TRANSACTIONAL', 'Transactional'), ('MARKETING', 'Marketing'), ('OTP', 'OTP')], validators=[DataRequired()])
    header_type = SelectField('Header Type', choices=[('NONE', 'None'), ('TEXT', 'Text'), ('IMAGE', 'Image')], default='NONE')
    header_text = StringField('Header Text')
    header_image_url = StringField('Header Image URL')
    footer_text = StringField('Footer Text')
    # Button fields (up to 3)
    button1_type = SelectField('Button 1 Type', choices=[('', 'None'), ('QUICK_REPLY', 'Quick Reply'), ('CALL_TO_ACTION', 'Call To Action')], default='')
    button1_text = StringField('Button 1 Text')
    button1_url = StringField('Button 1 URL')
    button2_type = SelectField('Button 2 Type', choices=[('', 'None'), ('QUICK_REPLY', 'Quick Reply'), ('CALL_TO_ACTION', 'Call To Action')], default='')
    button2_text = StringField('Button 2 Text')
    button2_url = StringField('Button 2 URL')
    button3_type = SelectField('Button 3 Type', choices=[('', 'None'), ('QUICK_REPLY', 'Quick Reply'), ('CALL_TO_ACTION', 'Call To Action')], default='')
    button3_text = StringField('Button 3 Text')
    button3_url = StringField('Button 3 URL')
    content = TextAreaField('Message Content', validators=[DataRequired()])
    submit = SubmitField('Create Template')
