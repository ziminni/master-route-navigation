# Utils Package - Document Management System

This package provides utility functions and classes for the Document Management interface.

---

## Modules

### `icon_utils.py`

Provides utilities for loading and managing icons from the Assets folder.

### `role_utils.py`

**NEW!** Provides utilities for role-based routing and permission checking with hierarchical sub-role support.

**Key Features:**
- ✅ Hierarchical role system (Primary roles + Sub-roles)
- ✅ Automatic dashboard routing based on roles
- ✅ Fine-grained permission checking
- ✅ Support for custom sub-role permissions

**Supported Roles:**
- **Admin**: admin, super_admin, administrator
- **Faculty**: faculty, dean, professor, instructor, teacher
- **Staff**: staff, registrar, hr, clerk, secretary
- **Student**: student, org_officer, officer, learner

---

## Icon Utilities

### `IconLoader` Class

A comprehensive utility class for managing icons throughout the application.

#### Methods:

##### `load_icon(icon_name, size=None, cache=True)`
Load an icon from the Assets folder.

**Parameters:**
- `icon_name` (str): Name of the icon file (e.g., 'menu-burger.png')
- `size` (tuple): Optional (width, height) tuple to scale the icon
- `cache` (bool): Whether to cache the loaded icon (default: True)

**Returns:** `QPixmap` or `None` if failed

**Example:**
```python
from utils.icon_utils import IconLoader

# Load icon without scaling
icon = IconLoader.load_icon('menu-burger.png')

# Load icon with scaling
icon = IconLoader.load_icon('search.png', size=(20, 20))
```

---

##### `create_icon_button(icon_name, size=(24,24), button_size=None, flat=True, tooltip=None, callback=None)`
Create a QPushButton with an icon.

**Parameters:**
- `icon_name` (str): Name of the icon file
- `size` (tuple): Icon size (width, height) - default: (24, 24)
- `button_size` (tuple): Button size (width, height) - optional
- `flat` (bool): Flat button style (no border) - default: True
- `tooltip` (str): Tooltip text - optional
- `callback` (callable): Click handler function - optional

**Returns:** `QPushButton`

**Example:**
```python
from utils.icon_utils import IconLoader

# Create a simple icon button
btn = IconLoader.create_icon_button('menu-burger.png')

# Create with all options
btn = IconLoader.create_icon_button(
    'search.png',
    size=(20, 20),
    button_size=(32, 32),
    flat=False,
    tooltip="Search documents",
    callback=lambda: print("Search clicked")
)
```

---

##### `create_icon_label(icon_name, size=(24,24), alignment=None)`
Create a QLabel displaying an icon.

**Parameters:**
- `icon_name` (str): Name of the icon file
- `size` (tuple): Icon size (width, height) - default: (24, 24)
- `alignment` (Qt.AlignmentFlag): Label alignment - optional

**Returns:** `QLabel`

**Example:**
```python
from utils.icon_utils import IconLoader
from PyQt6.QtCore import Qt

label = IconLoader.create_icon_label(
    'folder.png',
    size=(32, 32),
    alignment=Qt.AlignmentFlag.AlignCenter
)
```

---

##### `get_qicon(icon_name, size=None)`
Get a QIcon object (useful for window icons, menu items, etc.).

**Parameters:**
- `icon_name` (str): Name of the icon file
- `size` (tuple): Optional icon size

**Returns:** `QIcon`

**Example:**
```python
from utils.icon_utils import IconLoader

icon = IconLoader.get_qicon('menu-burger.png', size=(16, 16))
action.setIcon(icon)  # For menu items
```

---

##### `clear_cache()`
Clear the icon cache to free up memory.

**Example:**
```python
IconLoader.clear_cache()
```

---

### Convenience Functions

Pre-configured functions for common icons.

#### `create_menu_button(callback=None)`
Create a menu (hamburger) button with standard styling.

**Parameters:**
- `callback` (callable): Optional click handler

**Returns:** `QPushButton` (24x24 icon, 32x32 button, flat style)

**Example:**
```python
from utils.icon_utils import create_menu_button

menu_btn = create_menu_button(callback=lambda: print("Menu clicked"))
```

---

#### `create_search_button(callback=None)`
Create a search button with standard styling.

**Parameters:**
- `callback` (callable): Optional click handler

**Returns:** `QPushButton` (20x20 icon, 32x32 button, normal style)

**Example:**
```python
from utils.icon_utils import create_search_button

search_btn = create_search_button(callback=self.handle_search)
```

---

## Usage in Views

### Simple Usage (Recommended)

```python
from ...utils.icon_utils import create_menu_button, create_search_button

class MyView(QWidget):
    def init_ui(self):
        # Create menu button
        menu_btn = create_menu_button(callback=self.show_menu)
        
        # Create search button
        search_btn = create_search_button(callback=self.do_search)
```

### Advanced Usage

```python
from ...utils.icon_utils import IconLoader

class MyView(QWidget):
    def init_ui(self):
        # Custom icon button
        custom_btn = IconLoader.create_icon_button(
            'custom-icon.png',
            size=(28, 28),
            button_size=(40, 40),
            flat=True,
            tooltip="Custom Action",
            callback=self.custom_action
        )
        
        # Icon label
        icon_label = IconLoader.create_icon_label(
            'folder.png',
            size=(48, 48),
            alignment=Qt.AlignmentFlag.AlignCenter
        )
```

---

## Features

✅ **Automatic Path Resolution** - No need to worry about relative paths  
✅ **Icon Caching** - Loaded icons are cached for performance  
✅ **Fallback Support** - Displays text if icon fails to load  
✅ **Smooth Scaling** - High-quality icon scaling  
✅ **Flexible** - Works with buttons, labels, and QIcon objects  
✅ **Clean API** - Simple convenience functions for common use cases  

---

## Supported Icons

Current icons in the Assets folder:
- `menu-burger.png` - Hamburger menu icon
- `search.png` - Search icon

**Adding New Icons:**
1. Place PNG file in `Assets/` folder
2. Use with `IconLoader` or create convenience function
3. Update fallback map in `_get_fallback_text()` if desired

---

## Fallback System

If an icon fails to load, the system automatically provides text fallbacks:

| Icon File | Fallback |
|-----------|----------|
| menu-burger.png | ☰ |
| search.png | 🔍 |
| add.png | + |
| delete.png | 🗑 |
| edit.png | ✏ |
| save.png | 💾 |
| download.png | ⬇ |
| upload.png | ⬆ |
| folder.png | 📁 |
| file.png | 📄 |

---

## Performance Notes

- Icons are cached after first load
- Caching can be disabled per-call if needed
- Call `IconLoader.clear_cache()` to free memory if needed
- Cached icons are stored as QPixmap objects

---

## Best Practices

1. **Use convenience functions** for standard icons (menu, search)
2. **Cache icons** for frequently used images
3. **Specify tooltips** for icon-only buttons (accessibility)
4. **Use consistent sizes** throughout your interface
5. **Test fallbacks** by temporarily renaming icon files

---

## Future Enhancements

Potential additions:
- Theme support (light/dark icons)
- SVG icon support
- Icon color tinting
- Animation support
- More convenience functions for common icons
