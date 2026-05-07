import { useStyles } from "components/loader/styles";
import { AiOutlineLoading3Quarters } from "react-icons/ai";
import { keyframes } from "@emotion/react";
import { styled } from "@mui/material/styles";

const Keyframes = keyframes`
  0% {transform: rotate(0deg)}
  100% {transform: rotate(360deg)}
`;

const AnimatedLoaderIcon = styled((props) => (
  <AiOutlineLoading3Quarters {...props} />
))(() => ({
  animation: `${Keyframes} 1s linear infinite`,
}));

const Loader = () => {
  const { classes: styles } = useStyles();
  return (
    <div className={styles.loader}>
      <AnimatedLoaderIcon />
    </div>
  );
};

export default Loader;
