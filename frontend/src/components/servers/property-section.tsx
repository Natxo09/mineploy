"use client";

import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { PropertyField } from "./property-field";
import type { ServerProperties } from "@/types";
import type { PropertyMetadata } from "./property-metadata";

interface PropertySectionProps {
  category: string;
  metadata: PropertyMetadata[];
  formData: Partial<ServerProperties>;
  onChange: (key: keyof ServerProperties, value: any) => void;
}

export function PropertySection({
  category,
  metadata,
  formData,
  onChange,
}: PropertySectionProps) {
  return (
    <AccordionItem value={category}>
      <AccordionTrigger className="text-base font-medium">
        {category}
      </AccordionTrigger>
      <AccordionContent>
        <div className="grid gap-4 pt-4">
          {metadata.map((meta) => (
            <PropertyField
              key={meta.key}
              metadata={meta}
              value={formData[meta.key]}
              onChange={(value) => onChange(meta.key, value)}
            />
          ))}
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
