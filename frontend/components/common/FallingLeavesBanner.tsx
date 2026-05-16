"use client";

import {
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
} from "react";

const LEAF_COLORS = ["#2E7D32", "#4CAF50", "#1b5e20", "#388e3c"];

type LeafParticle = {
  x: number;
  y: number;
  size: number;
  rotation: number;
  rotationSpeed: number;
  speedY: number;
  drift: number;
  swayPhase: number;
  swaySpeed: number;
  opacity: number;
  color: string;
};

function leafCountForArea(width: number, height: number) {
  return Math.min(96, Math.max(52, Math.floor((width * height) / 11_000)));
}

function randomBetween(min: number, max: number) {
  return min + Math.random() * (max - min);
}

function createLeaf(width: number, height: number): LeafParticle {
  return {
    x: randomBetween(0, width),
    y: randomBetween(-height * 1.2, height * 0.85),
    size: randomBetween(8, 20),
    rotation: randomBetween(0, Math.PI * 2),
    rotationSpeed: randomBetween(-0.025, 0.025),
    speedY: randomBetween(0.55, 1.75),
    drift: randomBetween(-0.25, 0.25),
    swayPhase: randomBetween(0, Math.PI * 2),
    swaySpeed: randomBetween(0.008, 0.02),
    opacity: randomBetween(0.2, 0.5),
    color: LEAF_COLORS[Math.floor(Math.random() * LEAF_COLORS.length)],
  };
}

function drawLeaf(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  size: number,
  rotation: number,
  color: string,
  opacity: number,
) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rotation);
  ctx.globalAlpha = opacity;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, -size);
  ctx.bezierCurveTo(size * 0.65, -size * 0.35, size * 0.55, size * 0.55, 0, size);
  ctx.bezierCurveTo(-size * 0.55, size * 0.55, -size * 0.65, -size * 0.35, 0, -size);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

type FallingLeavesBannerProps = {
  children: ReactNode;
  className?: string;
  contentClassName?: string;
};

export function FallingLeavesBanner({
  children,
  className = "",
  contentClassName = "",
}: FallingLeavesBannerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const leavesRef = useRef<LeafParticle[]>([]);
  const frameRef = useRef<number>(0);
  const sizeRef = useRef({ width: 0, height: 0 });

  const initLeaves = useCallback((width: number, height: number) => {
    const count = leafCountForArea(width, height);
    leavesRef.current = Array.from({ length: count }, () =>
      createLeaf(width, height),
    );
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    const resize = () => {
      const { width, height } = container.getBoundingClientRect();
      if (width === 0 || height === 0) return;

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const prev = sizeRef.current;
      sizeRef.current = { width, height };
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const sizeChanged =
        Math.abs(prev.width - width) > 48 || Math.abs(prev.height - height) > 48;

      if (leavesRef.current.length === 0 || sizeChanged) {
        initLeaves(width, height);
      }
    };

    resize();
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);

    const tick = () => {
      const { width, height } = sizeRef.current;
      if (width === 0 || height === 0) {
        frameRef.current = requestAnimationFrame(tick);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      if (!prefersReducedMotion) {
        for (const leaf of leavesRef.current) {
          leaf.swayPhase += leaf.swaySpeed;
          leaf.x += leaf.drift + Math.sin(leaf.swayPhase) * 0.35;
          leaf.y += leaf.speedY;
          leaf.rotation += leaf.rotationSpeed;

          if (leaf.y - leaf.size > height) {
            Object.assign(leaf, createLeaf(width, height));
            leaf.y = -leaf.size * 2;
          }

          if (leaf.x < -leaf.size) leaf.x = width + leaf.size;
          if (leaf.x > width + leaf.size) leaf.x = -leaf.size;

          drawLeaf(
            ctx,
            leaf.x,
            leaf.y,
            leaf.size,
            leaf.rotation,
            leaf.color,
            leaf.opacity,
          );
        }
      }

      frameRef.current = requestAnimationFrame(tick);
    };

    frameRef.current = requestAnimationFrame(tick);

    return () => {
      resizeObserver.disconnect();
      cancelAnimationFrame(frameRef.current);
    };
  }, [initLeaves]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden ${className}`}
    >
      <canvas
        ref={canvasRef}
        className="pointer-events-none absolute inset-0 z-10 h-full w-full"
        aria-hidden
      />
      <div
        className={`relative z-20 flex w-full min-h-0 flex-col ${contentClassName}`}
      >
        {children}
      </div>
    </div>
  );
}
