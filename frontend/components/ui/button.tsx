import Link from "next/link";
import type { ReactNode } from "react";

interface ButtonProps {
  onClick?: () => void;
  onSubmit?: () => void;
  className?: string;
  children: ReactNode;
  href?: string;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  loading?: boolean;
  icon?: ReactNode;
  iconPosition?: "left" | "right";
  iconSize?: number;
}

const defaultClassName =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-[#2E7D32] px-8 py-3.5 text-base font-medium text-white transition-colors hover:bg-[#1b5e20] disabled:cursor-not-allowed disabled:opacity-50";

export default function CommonButton({
  children,
  href,
  className,
  onClick,
  onSubmit,
  type = "button",
  disabled,
  loading,
  icon,
  iconPosition = "right",
  iconSize,
}: ButtonProps) {
  const classes = className ?? defaultClassName;

  const iconNode =
    icon &&
    (iconSize ? (
      <span
        className="inline-flex shrink-0 items-center justify-center"
        style={{ width: iconSize, height: iconSize }}
      >
        {icon}
      </span>
    ) : (
      icon
    ));

  const content = (
    <>
      {icon && iconPosition === "left" && iconNode}
      {loading ? "Loading..." : children}
      {icon && iconPosition === "right" && iconNode}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={classes}>
        {content}
      </Link>
    );
  }

  const handleClick = () => {
    onClick?.();
    onSubmit?.();
  };

  return (
    <button
      type={type}
      onClick={onClick || onSubmit ? handleClick : undefined}
      disabled={disabled || loading}
      className={classes}
    >
      {content}
    </button>
  );
}
