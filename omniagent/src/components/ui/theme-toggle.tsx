import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, Monitor, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
  variant?: "icon" | "button" | "dropdown";
  showLabel?: boolean;
}

/**
 * Functional Night / Light Mode Toggle Button
 * Supports 1-click toggle between Dark and Light mode, or full Dropdown menu (Light/Dark/System).
 */
export function ThemeToggle({
  className,
  variant = "icon",
  showLabel = false,
}: ThemeToggleProps) {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const { t, language } = useI18n();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = resolvedTheme === "dark";

  // Cycle directly between light and dark on button click
  const handleToggle = () => {
    setTheme(isDark ? "light" : "dark");
  };

  const tooltipText = isDark
    ? (language === "fr" ? "Activer le mode clair" : "تفعيل الوضع النهاري")
    : (language === "fr" ? "Activer le mode sombre" : "تفعيل الوضع الليلي");

  // Prevent hydration layout shift
  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-9 w-9 rounded-lg opacity-70", className)}
        aria-label="Toggle theme"
        disabled
      >
        <Sun className="h-4 w-4" />
      </Button>
    );
  }

  // Dropdown menu variant
  if (variant === "dropdown") {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size={showLabel ? "default" : "icon"}
            className={cn("h-9 rounded-lg gap-2 relative", className)}
            aria-label={t("theme.toggle")}
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0 text-amber-500" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100 text-sky-400" />
            {showLabel && (
              <span className="text-sm font-medium">
                {theme === "dark"
                  ? t("theme.dark")
                  : theme === "light"
                  ? t("theme.light")
                  : t("theme.system")}
              </span>
            )}
            <span className="sr-only">{t("theme.toggle")}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-40 z-50">
          <DropdownMenuItem
            onClick={() => setTheme("light")}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <Sun className="h-4 w-4 text-amber-500" />
              <span>{t("theme.light")}</span>
            </span>
            {theme === "light" && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => setTheme("dark")}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <Moon className="h-4 w-4 text-sky-400" />
              <span>{t("theme.dark")}</span>
            </span>
            {theme === "dark" && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => setTheme("system")}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <Monitor className="h-4 w-4 text-muted-foreground" />
              <span>{t("theme.system")}</span>
            </span>
            {theme === "system" && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  // 1-Click Interactive Toggle Button (with Tooltip)
  const buttonContent = (
    <Button
      variant="ghost"
      size={showLabel ? "default" : "icon"}
      onClick={handleToggle}
      className={cn(
        "h-9 rounded-lg gap-2 relative transition-all duration-200 hover:bg-muted/80 text-foreground",
        showLabel ? "px-3" : "w-9",
        className
      )}
      aria-label={tooltipText}
    >
      <div className="relative flex items-center justify-center w-4 h-4">
        <Sun className="h-4 w-4 rotate-0 scale-100 transition-all duration-300 dark:-rotate-90 dark:scale-0 text-amber-500" />
        <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all duration-300 dark:rotate-0 dark:scale-100 text-sky-400" />
      </div>
      {showLabel && (
        <span className="text-sm font-medium">
          {isDark ? t("theme.dark") : t("theme.light")}
        </span>
      )}
      <span className="sr-only">{tooltipText}</span>
    </Button>
  );

  if (showLabel) {
    return buttonContent;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{buttonContent}</TooltipTrigger>
      <TooltipContent side="bottom">
        <p className="text-xs">{tooltipText}</p>
      </TooltipContent>
    </Tooltip>
  );
}
