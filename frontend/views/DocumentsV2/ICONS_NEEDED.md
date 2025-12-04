# Icons Needed for DocumentsV2 App

This document lists all the icons needed for the Documents application. For now, we're using emojis as placeholders, but you'll need to download/create actual icons for production.

## 📁 File Type Icons (16x16 or 24x24 px)

### Documents
- `icon_pdf.png` - PDF files (📄)
- `icon_doc.png` - Word documents (📝)
- `icon_docx.png` - Word documents (📝)
- `icon_txt.png` - Text files (📃)

### Spreadsheets
- `icon_xls.png` - Excel files (📊)
- `icon_xlsx.png` - Excel files (📊)
- `icon_csv.png` - CSV files (📊)

### Presentations
- `icon_ppt.png` - PowerPoint (📽️)
- `icon_pptx.png` - PowerPoint (📽️)

### Images
- `icon_jpg.png` - JPEG images (🖼️)
- `icon_png.png` - PNG images (🖼️)
- `icon_gif.png` - GIF images (🖼️)
- `icon_svg.png` - SVG images (🎨)

### Archives
- `icon_zip.png` - ZIP archives (📦)
- `icon_rar.png` - RAR archives (📦)
- `icon_7z.png` - 7-Zip archives (📦)

### Code
- `icon_py.png` - Python files (🐍)
- `icon_js.png` - JavaScript files (📜)
- `icon_html.png` - HTML files (🌐)
- `icon_css.png` - CSS files (🎨)

### Other
- `icon_folder.png` - Folders (📁)
- `icon_file.png` - Generic file (📄)

---

## 🎯 Navigation Icons (24x24 px)

### Sidebar Navigation
- `nav_mydrive.png` - My Drive (💾)
- `nav_shared.png` - Shared with me (👥)
- `nav_recent.png` - Recent files (🕐)
- `nav_starred.png` - Starred/Featured (⭐)
- `nav_trash.png` - Trash bin (🗑️)

### Categories (can use folder icon with different colors)
- `category_academic.png` - Academic (🎓)
- `category_admin.png` - Administration (⚙️)
- `category_forms.png` - Forms (📋)
- `category_general.png` - General (📂)

---

## 🛠️ Toolbar Icons (20x20 or 24x24 px)

### Main Actions
- `action_new.png` - New/Create (➕)
- `action_upload.png` - Upload file (⬆️)
- `action_newfolder.png` - New folder (📁➕)
- `action_refresh.png` - Refresh (🔄)

### View Controls
- `view_list.png` - List view (☰)
- `view_grid.png` - Grid view (⊞) [not used yet]

### Sort & Filter
- `action_sort.png` - Sort dropdown (⇅)
- `action_filter.png` - Filter (🔍)
- `action_search.png` - Search (🔎)

---

## 📋 Context Menu Icons (16x16 px)

### File Actions
- `menu_open.png` - Open file (📂)
- `menu_download.png` - Download (⬇️)
- `menu_move.png` - Move to folder (📤)
- `menu_rename.png` - Rename (✏️)
- `menu_star.png` - Add to starred (⭐)
- `menu_delete.png` - Delete/Move to trash (🗑️)

### Info & Sharing
- `menu_info.png` - File details (ℹ️)
- `menu_share.png` - Share (👥)
- `menu_link.png` - Get link (🔗)

---

## 💬 Status & Approval Icons (16x16 px)

### Approval Status
- `status_pending.png` - Pending approval (🟡)
- `status_approved.png` - Approved (✅)
- `status_rejected.png` - Rejected (❌)
- `status_resubmitted.png` - Resubmitted (🔄)

### File Status
- `status_public.png` - Public access (🌐)
- `status_private.png` - Private/Restricted (🔒)
- `status_shared.png` - Shared (👥)

---

## 🎨 UI Elements (various sizes)

### Buttons
- `btn_close.png` - Close/Cancel (✖️)
- `btn_back.png` - Back/Return (◀️)
- `btn_forward.png` - Forward (▶️)
- `btn_more.png` - More options (⋮)

### Notifications
- `notif_success.png` - Success message (✓)
- `notif_error.png` - Error message (⚠️)
- `notif_info.png` - Information (ℹ️)
- `notif_warning.png` - Warning (⚠️)

---

## 📊 Dashboard Icons (32x32 or 48x48 px)

### Statistics Cards
- `card_documents.png` - Total documents (📄)
- `card_storage.png` - Storage usage (💾)
- `card_approvals.png` - Pending approvals (⏳)
- `card_recent.png` - Recent activity (📈)

---

## 🎭 User Role Badges (16x16 px)

- `role_admin.png` - Admin (👑)
- `role_faculty.png` - Faculty (👨‍🏫)
- `role_staff.png` - Staff (👔)
- `role_student.png` - Student (🎓)

---

## 📦 Recommended Icon Packs/Sources

1. **Material Design Icons** - https://materialdesignicons.com/
   - Free, comprehensive, consistent style
   - Good for UI elements

2. **Feather Icons** - https://feathericons.com/
   - Clean, minimal, stroke-based
   - Great for toolbars

3. **Heroicons** - https://heroicons.com/
   - Tailwind CSS icons
   - Modern, clean design

4. **Font Awesome** - https://fontawesome.com/
   - Huge library
   - Free tier available

5. **Flaticon** - https://www.flaticon.com/
   - Millions of icons
   - Various styles
   - Attribution required for free tier

---

## 🎨 Icon Style Guidelines

### Consistency
- Use same icon pack/style throughout
- Keep sizes consistent (16px, 24px, 32px)
- Maintain visual weight balance

### Colors
- Primary actions: Blue/Green tones
- Destructive actions (delete): Red tones
- Neutral actions: Gray tones
- Status colors:
  - Success: Green (#4CAF50)
  - Warning: Yellow (#FFC107)
  - Error: Red (#F44336)
  - Info: Blue (#2196F3)

### Format
- **PNG** with transparency for most icons
- **SVG** for scalability (preferred)
- **ICO** for Windows-specific icons

### File Naming Convention
```
{category}_{name}_{size}.{ext}
Examples:
- nav_mydrive_24.png
- action_upload_24.svg
- status_approved_16.png
```

---

## 📥 Quick Setup Commands

Once you have icons downloaded:

```bash
# Create icons directory
mkdir -p frontend/assets/icons

# Organize by category
mkdir -p frontend/assets/icons/{file_types,navigation,actions,status,ui}

# Copy icons to respective folders
# file_types/ - PDF, DOC, XLS icons
# navigation/ - Sidebar icons
# actions/ - Toolbar icons
# status/ - Status badges
# ui/ - General UI elements
```

---

## 🔄 Migration from Emojis

When ready to use real icons, update in:
1. `widgets/sidebar.py` - Navigation icons
2. `widgets/file_list.py` - File type icons
3. `widgets/toolbar.py` - Action icons
4. `dialogs/upload_dialog.py` - Upload UI icons
5. `main_window.py` - Window icons

Search for emoji usage: `grep -r "📄\|📁\|⬆️" frontend/views/DocumentsV2/`
