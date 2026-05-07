
import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: {
      main: "#474DA4",
    },
    secondary: {
      main: "#2EC4B6",
      contrastText: "#fff",
    },
  },
  custom: {
    background: {
      main: "#474DA4",
    },
    font: {
      main: "#ffffff",
    }
  },
  components: {
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
          border: "1px solid #E2E8F0"
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
            backgroundColor: "#fff",
            color: "#474DA4"
          },
        },
        root: {
          textTransform: "capitalize",
          textDecoration: "none",
        },
      }
    },
    MuiButtonBase: {
      styleOverrides: {
        padding: "inherit"
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
      "@media (max-width:600px)": {
        fontSize: "12px",
      },
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
      fontWeight: 500
    },
    p: {
      fontFamily: "Lato",
      fontWeight: 400
    }
  }
})

export { theme }