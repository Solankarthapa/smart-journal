import React, { useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    glowColor?: string;
    tilt?: boolean;
}

export function GlassCard({ children, className, glowColor, tilt = true }: GlassCardProps) {
    const cardRef = useRef<HTMLDivElement>(null);
    const [transform, setTransform] = useState("rotateX(0deg) rotateY(0deg)");

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!tilt || !cardRef.current) return;
        const rect = cardRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -8;
        const rotateY = ((x - centerX) / centerX) * 8;
        setTransform(`rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`);
    };

    const handleMouseLeave = () => {
        setTransform("rotateX(0deg) rotateY(0deg) scale(1)");
    };

    return (
        <div
            ref={cardRef}
            className={cn("glass-card", className)}
            style={{ transform, transformStyle: "preserve-3d" }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
        >
            {glowColor && (
                <div
                    className="stat-glow"
                    style={{ background: `radial-gradient(circle, ${glowColor} 0%, transparent 70%)` }}
                />
            )}
            <div className="relative z-10">{children}</div>
        </div>
    );
}