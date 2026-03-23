import type { GlobalThemeOverrides } from 'naive-ui'

/**
 * Спокойная тёмная тема: холодный графит, мягкие бирюза/янтарь,
 * единые радиусы и тени для карточек и навигации.
 */
export const naiveThemeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily:
      '"Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    fontFamilyMono: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    fontSize: '15px',
    fontSizeMini: '11px',
    fontSizeTiny: '12px',
    fontSizeSmall: '13px',
    fontSizeMedium: '15px',
    fontSizeLarge: '17px',
    fontSizeHuge: '20px',
    lineHeight: '1.55',
    borderRadius: '12px',
    borderRadiusSmall: '8px',
    heightMedium: '40px',
    heightSmall: '32px',

    primaryColor: '#34d3c0',
    primaryColorHover: '#4ddccb',
    primaryColorPressed: '#2bb8a8',
    primaryColorSuppl: '#34d3c0',

    warningColor: '#e8b86d',
    warningColorHover: '#efc47f',
    warningColorPressed: '#d9a85a',
    warningColorSuppl: '#e8b86d',

    successColor: '#34d3c0',
    infoColor: '#7c9eff',

    bodyColor: '#e8eaef',
    textColorBase: '#e8eaef',
    textColor1: 'rgba(232, 234, 239, 0.95)',
    textColor2: '#9aa3b5',
    textColor3: '#6b7289',

    cardColor: 'rgba(22, 26, 36, 0.92)',
    modalColor: '#161a24',
    popoverColor: '#1a1f2e',
    tableColor: '#161a24',

    hoverColor: 'rgba(255, 255, 255, 0.055)',
    pressedColor: 'rgba(255, 255, 255, 0.08)',
    borderColor: 'rgba(255, 255, 255, 0.065)',
    dividerColor: 'rgba(255, 255, 255, 0.07)',
  },

  Layout: {
    color: '#07090e',
    colorEmbedded: '#07090e',
    headerColor: 'rgba(10, 12, 18, 0.72)',
    headerBorderColor: 'rgba(255, 255, 255, 0.06)',
    textColor: '#e8eaef',
  },

  Menu: {
    borderRadius: '10px',
    fontSize: '13px',
    itemHeight: '36px',
    itemColorHover: 'rgba(255, 255, 255, 0.06)',
    itemColorActive: 'rgba(52, 211, 192, 0.14)',
    itemColorActiveHover: 'rgba(52, 211, 192, 0.2)',
    itemTextColorHorizontal: '#9aa3b5',
    itemTextColorHoverHorizontal: '#e8eaef',
    itemTextColorActiveHorizontal: '#6ee7d8',
    itemTextColorActiveHoverHorizontal: '#8ef0e4',
    itemTextColorChildActiveHorizontal: '#6ee7d8',
    borderColorHorizontal: 'transparent',
    color: 'transparent',
  },

  Card: {
    color: 'rgba(20, 24, 34, 0.88)',
    borderColor: 'rgba(255, 255, 255, 0.07)',
    titleTextColor: '#f1f3f7',
    textColor: '#9aa3b5',
    titleFontWeight: '650',
    borderRadius: '16px',
    boxShadow: '0 8px 32px -12px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255,255,255,0.04) inset',
    paddingMedium: '22px',
    paddingLarge: '26px',
    titleFontSizeLarge: '1.25rem',
  },

  Button: {
    borderRadiusMedium: '10px',
    borderRadiusSmall: '8px',
    fontWeight: '600',
    heightMedium: '38px',
  },

  Tag: {
    borderRadius: '8px',
    fontWeightStrong: '650',
    colorPrimary: 'rgba(52, 211, 192, 0.14)',
    textColorPrimary: '#8ef0e4',
    borderPrimary: '1px solid rgba(52, 211, 192, 0.28)',
    colorWarning: 'rgba(232, 184, 109, 0.14)',
    textColorWarning: '#f2d9a8',
    borderWarning: '1px solid rgba(232, 184, 109, 0.28)',
  },

  Alert: {
    borderRadius: '14px',
    padding: '14px 16px',
  },

  Spin: {
    opacitySpinning: '0.45',
  },

  Divider: {
    color: 'rgba(255, 255, 255, 0.08)',
  },

  Empty: {
    textColor: '#6b7289',
  },

  Typography: {
    headerTextColor: '#f4f6fa',
    headerFontWeight: '650',
    pTextColor: '#9aa3b5',
    pTextColor1Depth: '#b8c0d0',
    pTextColor2Depth: '#9aa3b5',
    pTextColor3Depth: '#6b7289',
    pLineHeight: '1.7',
    pFontSize: '15px',
    headerFontSize1: '1.75rem',
    liTextColor: '#9aa3b5',
    codeBorderRadius: '8px',
    codeColor: 'rgba(0, 0, 0, 0.35)',
    codeBorder: '1px solid rgba(255,255,255,0.08)',
  },

  Image: {
    toolbarBorderRadius: '10px',
  },
}
