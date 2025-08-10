# Design Document

## Overview

The rebranding from WaBridge to Convoxio requires a systematic approach to update all brand references across the Flask application. Based on code analysis, the changes span across HTML templates, Python code, and potentially database content. The design ensures consistency while maintaining all existing functionality.

## Architecture

### Brand Reference Categories

The rebranding touches several architectural layers:

1. **Presentation Layer**: HTML templates, page titles, UI text
2. **Application Layer**: Flash messages, form labels, notifications
3. **Configuration Layer**: Application metadata, payment integration
4. **Data Layer**: Any stored brand references in templates or content

### Change Scope Analysis

From codebase analysis, the following files contain "WaBridge" references:
- **Templates**: 16 HTML template files with title blocks
- **Routes**: 1 Python file with flash message
- **Base Template**: Core branding in navigation and default title
- **Payment Integration**: Razorpay configuration with brand name

## Components and Interfaces

### Template System Updates

**Base Template (app/templates/base.html)**
- Update default title block from "WaBridge" to "Convoxio"
- Update navbar brand text from "WaBridge" to "Convoxio"
- Maintain existing Bootstrap and styling structure

**Individual Template Files**
- Update title blocks in all 16 template files
- Pattern: `{% block title %}[Page Name] - Convoxio{% endblock %}`
- Maintain existing template inheritance structure

### Application Code Updates

**Routes Module (app/routes.py)**
- Update welcome flash message from "Welcome to WaBridge!" to "Welcome to Convoxio!"
- Maintain existing functionality and user flow

**Payment Integration**
- Update Razorpay configuration name from "WaBridge" to "Convoxio"
- Ensure payment gateway displays correct brand name

### Brand Consistency Strategy

**Naming Convention**
- Primary brand: "Convoxio"
- Tagline options: "Connect with Your Customers Instantly" (maintain existing)
- Maintain WhatsApp integration messaging

**Visual Identity**
- Keep existing WhatsApp icon in navigation (bi-whatsapp)
- Maintain current color scheme and styling
- Update only text-based brand references

## Data Models

### Template Library Content

**Existing Template Variables**
- Keep `{{business_name}}` variable unchanged
- Keep `{{customer_name}}` variable unchanged
- These represent user's business, not the platform brand

**Seed Data**
- Review seed_templates.py for any platform brand references
- Update any hardcoded platform references to "Convoxio"

## Error Handling

### Brand Reference Validation

**Template Rendering**
- Ensure all templates render correctly after brand updates
- Validate title blocks display properly
- Test template inheritance chain

**User Experience**
- Maintain consistent brand experience across all user touchpoints
- Ensure no mixed branding (WaBridge/Convoxio) appears
- Validate payment flow shows correct brand name

## Testing Strategy

### Automated Testing Approach

**Template Testing**
- Verify all page titles contain "Convoxio"
- Check navbar displays "Convoxio" brand
- Validate no "WaBridge" references remain

**Integration Testing**
- Test payment flow with new brand name
- Verify flash messages show correct branding
- Test user registration and welcome flow

**Visual Regression Testing**
- Ensure UI layout remains unchanged
- Verify only text content is updated
- Check responsive design integrity

### Manual Testing Checklist

**Page-by-Page Verification**
- Dashboard: Title and branding
- Registration: Welcome message and title
- Login: Page title and form labels
- Template Library: Page title and navigation
- All other pages: Title consistency

**User Flow Testing**
- Registration → Welcome message shows "Convoxio"
- Payment → Razorpay shows "Convoxio"
- Navigation → Brand name consistent across pages

### Browser Compatibility

**Title and Metadata**
- Test browser tab titles show "Convoxio"
- Verify bookmark titles use new brand
- Check meta tags for SEO consistency

## Implementation Phases

### Phase 1: Core Template Updates
- Update base.html with primary branding
- Update all template title blocks
- Test template inheritance

### Phase 2: Application Logic Updates
- Update flash messages in routes.py
- Update payment integration branding
- Test user-facing messages

### Phase 3: Content and Data Updates
- Review and update any seed data
- Check for stored brand references
- Update configuration files if needed

### Phase 4: Validation and Testing
- Comprehensive testing across all pages
- User flow validation
- Cross-browser testing

## Rollback Strategy

### Change Tracking
- Document all modified files
- Maintain backup of original brand references
- Use version control for easy rollback

### Validation Points
- Each phase includes validation checkpoint
- Immediate rollback if functionality breaks
- Staged deployment approach recommended