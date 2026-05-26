#!/usr/bin/env bash
# release.sh — tag, push to GitHub, update AUR
#
# Usage:
#   ./release.sh 1.1.0        # explicit version
#   ./release.sh              # auto-bump patch  (1.0.0 → 1.0.1)
#   ./release.sh --aur-only   # only push PKGBUILD to AUR (no new GitHub tag)
#
# Remotes expected:
#   origin  → https://github.com/Varionetzwerk/hwsonnet.git
#   aur     → ssh://aur@aur.archlinux.org/hwsonnet.git

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKGBUILD="$ROOT/aur/PKGBUILD"
SRCINFO="$ROOT/aur/.SRCINFO"
GITHUB_REPO="Varionetzwerk/hwsonnet"
AUR_PKG="hwsonnet"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }
warn() { echo -e "${YELLOW}!${RESET} $*"; }
die()  { echo -e "${RED}✗${RESET} $*" >&2; exit 1; }

# ── Args ──────────────────────────────────────────────────────────────────────
AUR_ONLY=false
NEW_VERSION=""

for arg in "$@"; do
    case "$arg" in
        --aur-only) AUR_ONLY=true ;;
        [0-9]*.*.*) NEW_VERSION="$arg" ;;
        *) die "Unknown argument: '$arg'\nUsage: $0 [VERSION] [--aur-only]" ;;
    esac
done

cd "$ROOT"

# ── Git sanity ────────────────────────────────────────────────────────────────
git rev-parse --git-dir &>/dev/null || die "Not a git repository."

if ! git remote get-url origin &>/dev/null; then
    die "No 'origin' remote found. Run:\n  git remote add origin https://github.com/$GITHUB_REPO.git"
fi

# ── push_aur function ─────────────────────────────────────────────────────────
push_aur() {
    local ver="${1:-}"
    if ! git remote get-url aur &>/dev/null; then
        warn "No 'aur' remote configured — skipping AUR push."
        echo ""
        echo "  To enable AUR publishing, run once:"
        echo -e "  ${CYAN}git remote add aur ssh://aur@aur.archlinux.org/$AUR_PKG.git${RESET}"
        return
    fi

    local AUR_TMPDIR
    AUR_TMPDIR=$(mktemp -d)
    trap "rm -rf '$AUR_TMPDIR'" EXIT

    info "Cloning AUR repo..."
    local AUR_URL
    AUR_URL=$(git remote get-url aur)
    git clone "$AUR_URL" "$AUR_TMPDIR/aur" 2>/dev/null || {
        mkdir -p "$AUR_TMPDIR/aur"
        git -C "$AUR_TMPDIR/aur" init
        git -C "$AUR_TMPDIR/aur" remote add origin "$AUR_URL"
    }

    # Update pkgver in PKGBUILD
    if [[ -n "${ver:-}" ]]; then
        info "Updating pkgver to $ver in PKGBUILD..."
        sed -i "s/^pkgver=.*/pkgver=$ver/" "$PKGBUILD"
        sed -i "s/^	pkgver =.*/	pkgver = $ver/" "$SRCINFO"
        sed -i "s/#tag=v[0-9.]*/\#tag=v$ver/" "$PKGBUILD"
        sed -i "s/#tag=v[0-9.]*/\#tag=v$ver/" "$SRCINFO"
        ok "PKGBUILD pkgver → $ver"
    fi

    # Regenerate .SRCINFO if makepkg is available
    if command -v makepkg &>/dev/null; then
        info "Regenerating .SRCINFO..."
        (cd "$ROOT/aur" && makepkg --printsrcinfo > .SRCINFO)
        ok ".SRCINFO regenerated"
    fi

    cp "$PKGBUILD" "$AUR_TMPDIR/aur/PKGBUILD"
    cp "$SRCINFO"  "$AUR_TMPDIR/aur/.SRCINFO"

    git -C "$AUR_TMPDIR/aur" add PKGBUILD .SRCINFO
    if git -C "$AUR_TMPDIR/aur" diff --cached --quiet; then
        warn "AUR: PKGBUILD/.SRCINFO unchanged — nothing to push"
    else
        local tag_msg="${ver:+update to v$ver}"
        tag_msg="${tag_msg:-sync PKGBUILD}"
        git -C "$AUR_TMPDIR/aur" commit -m "$tag_msg"
        git -C "$AUR_TMPDIR/aur" push origin master
        ok "AUR updated → https://aur.archlinux.org/packages/$AUR_PKG"
    fi
}

# ── AUR-only shortcut ─────────────────────────────────────────────────────────
if $AUR_ONLY; then
    push_aur ""
    exit 0
fi

# ── Determine version ─────────────────────────────────────────────────────────
if [[ -z "$NEW_VERSION" ]]; then
    LAST=$(git tag --sort=-v:refname 2>/dev/null | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | head -1 || true)
    if [[ -z "$LAST" ]]; then
        NEW_VERSION="1.0.0"
        warn "No existing tags — using $NEW_VERSION"
    else
        LAST_CLEAN="${LAST#v}"
        IFS='.' read -r MAJOR MINOR PATCH <<< "$LAST_CLEAN"
        PATCH=$((PATCH + 1))
        NEW_VERSION="$MAJOR.$MINOR.$PATCH"
        info "Last tag: $LAST  →  auto bump: $NEW_VERSION"
    fi
fi

TAG="v$NEW_VERSION"

# ── Confirm ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Release plan: ${CYAN}$TAG${RESET}"
echo ""
echo "  Steps:"
echo "    1. Commit all staged/unstaged changes"
echo "    2. Create git tag $TAG"
echo "    3. Push branch + tag → GitHub (origin)"
echo "    4. Update PKGBUILD pkgver → $NEW_VERSION"
echo "    5. Regenerate .SRCINFO"
echo "    6. Push PKGBUILD to AUR (if 'aur' remote exists)"
echo ""
echo -e "  Remotes:"
echo -e "    ${CYAN}origin${RESET}: $(git remote get-url origin 2>/dev/null || echo '(not set)')"
echo -e "    ${CYAN}aur   ${RESET}: $(git remote get-url aur 2>/dev/null || echo '(not set — AUR push skipped)')"
echo ""
read -rp "Proceed? [y/N] " CONFIRM
[[ "${CONFIRM,,}" == "y" ]] || { echo "Aborted."; exit 0; }
echo ""

# ── Stage & commit ────────────────────────────────────────────────────────────
if [[ -n "$(git status --porcelain)" ]]; then
    info "Staging all changes..."
    git add -A
    git commit -m "chore: release $TAG"
    ok "Committed"
else
    info "Working tree clean — no commit needed"
fi

# ── Tag ───────────────────────────────────────────────────────────────────────
if git rev-parse "$TAG" &>/dev/null 2>&1; then
    warn "Tag $TAG already exists — skipping tag creation"
else
    git tag -a "$TAG" -m "Release $TAG"
    ok "Tag $TAG created"
fi

# ── Push to GitHub ────────────────────────────────────────────────────────────
info "Pushing to GitHub..."
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push origin "$BRANCH" "$TAG"
ok "GitHub up to date → https://github.com/$GITHUB_REPO/releases/tag/$TAG"

# Create GitHub release if gh is available
if command -v gh &>/dev/null; then
    info "Creating GitHub release..."
    gh release create "$TAG" \
        --title "HWSonnet $NEW_VERSION" \
        --notes "## HWSonnet $NEW_VERSION

### Changes
- See commit history for details

### Installation
\`\`\`bash
# AUR (Arch Linux)
yay -S hwsonnet

# Manual
git clone https://github.com/$GITHUB_REPO
cd hwsonnet && ./install.sh
\`\`\`" \
        --latest 2>/dev/null && ok "GitHub release created" || warn "gh release create failed (release may already exist)"
fi

# ── AUR push ─────────────────────────────────────────────────────────────────
push_aur "$NEW_VERSION"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}  Released $TAG successfully!${RESET}"
echo ""
echo -e "  GitHub : https://github.com/$GITHUB_REPO/releases/tag/$TAG"
echo -e "  AUR    : https://aur.archlinux.org/packages/$AUR_PKG"
echo ""
echo -e "  Users can update with: ${CYAN}yay -Syu hwsonnet${RESET}"
echo ""
