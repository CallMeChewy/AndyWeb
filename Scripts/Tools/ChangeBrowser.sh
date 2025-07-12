#!/bin/bash

echo "📡 Detecting available browsers..."

ALT_BROWSERS=($(update-alternatives --list x-www-browser 2>/dev/null))
DESKTOP_ENTRIES=()
DISPLAY_NAMES=()

CURRENT_DEFAULT=$(xdg-settings get default-web-browser 2>/dev/null)
CURRENT_INDEX=-1

# Helper: determine if a .desktop file is a real browser
is_valid_browser_desktop() {
    local file="$1"
    grep -qiE '^Categories=.*WebBrowser' "$file" || return 1
    grep -q 'X-Brave-Component=true' "$file" && return 1
    [[ "$file" =~ keditbookmarks ]] && return 1
    [[ "$file" =~ settings ]] && return 1
    return 0
}

# Gather .desktop browser entries
for entry in /usr/share/applications/*.desktop /var/lib/flatpak/exports/share/applications/*.desktop ~/.local/share/applications/*.desktop; do
    [ -f "$entry" ] || continue
    if is_valid_browser_desktop "$entry"; then
        NAME=$(basename "$entry")
        FRIENDLY=$(grep -m1 -i '^Name=' "$entry" | cut -d= -f2-)
        DESKTOP_ENTRIES+=("$NAME")
        DISPLAY_NAMES+=("${FRIENDLY:-$NAME} [$NAME]")
    fi
done

# Combine into master options
ALL_OPTIONS=("${ALT_BROWSERS[@]}" "${DESKTOP_ENTRIES[@]}")
DISPLAY_LIST=("${ALT_BROWSERS[@]}" "${DISPLAY_NAMES[@]}")

echo ""
for i in "${!DISPLAY_LIST[@]}"; do
    label="${DISPLAY_LIST[$i]}"
    if [[ "${ALL_OPTIONS[$i]}" == "$CURRENT_DEFAULT" ]]; then
        echo "$((i+1)). $label (✅ current)"
        CURRENT_INDEX=$i
    else
        echo "$((i+1)). $label"
    fi
done

echo ""
read -p "🔧 Enter the number of the browser to set as default [Enter to keep current]: " CHOICE

# Just keep the current default
if [[ -z "$CHOICE" ]]; then
    echo -e "\n📎 No changes made."
    echo "✅ Your current default browser remains: ${DISPLAY_LIST[$CURRENT_INDEX]}"
    read -n 1 -s -r -p $'\nPress any key to close...'
    echo ""
    exit 0
fi

# Validate input
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt ${#ALL_OPTIONS[@]} ]; then
    echo -e "\n❌ Invalid choice. Aborting."
    read -n 1 -s -r -p $'\nPress any key to close...'
    echo ""
    exit 1
fi

SELECTED="${ALL_OPTIONS[$((CHOICE-1))]}"
SELECTED_NAME="${DISPLAY_LIST[$((CHOICE-1))]}"

echo -e "\n⚙️ Setting default browser to: $SELECTED_NAME"

if [[ "$SELECTED" == /* ]]; then
    sudo update-alternatives --set x-www-browser "$SELECTED"
fi

if [[ "$SELECTED" == *.desktop ]]; then
    xdg-settings set default-web-browser "$SELECTED"
    xdg-mime default "$SELECTED" x-scheme-handler/http
    xdg-mime default "$SELECTED" x-scheme-handler/https
fi

echo -e "\n✅ Default browser successfully set to: $SELECTED_NAME"
read -n 1 -s -r -p $'\nPress any key to close...'
echo ""
