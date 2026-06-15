
import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: {
      main: "#474DA4",
      dark: "#343986",
      light: "#EEF0FF",
      contrastText: "#FFFFFF",
    },
    secondary: {
      main: "#147D73",
      dark: "#0F6159",
      light: "#E5F6F3",
      contrastText: "#FFFFFF",
    },
    background: {
      default: "#F6F7FB",
      paper: "#FFFFFF",
    },
    text: {
      primary: "#1D2433",
      secondary: "#5F6B7A",
    },
    divider: "#DDE2EA",
    success: {
      main: "#237A43",
    },
    warning: {
      main: "#A95E00",
    },
    error: {
      main: "#B42318",
    },
  },
  custom: {
    background: {
      main: "#474DA4",
    },
    font: {
      main: "#ffffff",
    },
    surface: {
      muted: "#F6F7FB",
      selected: "#EEF0FF",
    },
    status: {
      successBackground: "#EAF6EE",
      warningBackground: "#FFF4E5",
      errorBackground: "#FDECEC",
      infoBackground: "#EDF4FF",
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: "#F6F7FB",
        },
        "*:focus-visible": {
          outline: "3px solid #7B83DB",
          outlineOffset: 2,
        },
      },
    },
    MuiDataGrid: {
      styleOverrides: {
        columnHeadersInner: {
          width: "100%"
        },
        columnHeaderRow: {
          width: "100%"
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "none",
          border: "1px solid #DDE2EA",
          borderRadius: 10,
        }
      }
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 15,
          ":last-child": {
            paddingBottom: 15
          }
        }
      }
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontSize: 14,
        }
      }
    },
    MuiFormLabel: {
      styleOverrides: {
        root: {
          fontFamily: "Lato",
          fontWeight: 500
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        containedPrimary: {
          backgroundColor: "#474DA4",
          "&:hover": {
            backgroundColor: "#343986",
          },
        },
        root: {
          textTransform: "capitalize",
          textDecoration: "none",
          borderRadius: 8,
          fontWeight: 700,
          minHeight: 40,
        },
      }
    },
    MuiButtonBase: {
      styleOverrides: {
        root: {
          "&.Mui-focusVisible": {
            outline: "3px solid #7B83DB",
            outlineOffset: 2,
          },
        },
      }
    },
    MuiTypography: {
      styleOverrides: {
        fontFamily: "Lato"
      }
    },
    MuiOutlinedInput: {
      styleOverrides: {
        notchedOutline: {
          borderColor: "#1E1E1E"
        },
        input: {
          borderRadius: "3px",
          padding: "10px 10px",
        }
      }
    },
    MuiAutocomplete: {
      styleOverrides: {
        notchedOutline: {
          borderColor: "#1E1E1E"
        },
        inputRoot: {
          borderRadius: "3px",
          padding: "5px 10px",
        }
      }
    },
    MuiRadio: {
      styleOverrides: {
        root: {
          padding: "4px 9px",
        },
      }
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: {
          marginLeft: 0,
        },
      }
    },
  },
  typography: {
    body1: {
      fontFamily: "Lato",
      fontSize: "14px",
      lineHeight: 1.5,
    },
    body2: {
      fontFamily: "Lato",
      fontSize: "14px",
      lineHeight: 1.45,
    },
    h1: {
      fontFamily: "Lato",
      fontSize: "32px",
      fontWeight: 700
    },
    h2: {
      fontFamily: "Lato",
      fontSize: "24px",
      fontWeight: 700
    },
    h3: {
      fontFamily: "Lato",
      fontSize: "20px",
      fontWeight: 500
    },
    h4: {
      fontFamily: "Lato",
      fontSize: "18px",
      fontWeight: 500
    },
    h5: {
      fontFamily: "Lato",
      fontSize: "16px",
      fontWeight: 500
    },
    h6: {
      fontFamily: "Lato",
      fontSize: "14px",
      fontWeight: 700
    },
    p: {
      fontFamily: "Lato",
      fontWeight: 400
    }
  }
})

export { theme }
