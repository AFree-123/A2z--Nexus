const SIZES = {
  sm: 165,
  md: 145,
  lg: 210,
  xl: 280,
};

export default function A2ZNexusLogo({ size = "md", className = "" }) {
  const width = SIZES[size] || SIZES.md;

  return (
    <img
      src="/assets/a2z-nexus-logo.png"
      alt="A2Z Nexus"
      draggable={false}
      className={`object-contain ${className}`}
      style={{ width, height: "auto" }}
    />
  );
}
