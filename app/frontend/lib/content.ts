import content from "@/content/en.json";

export type Content = typeof content;

export function pickContent<Section extends keyof Content>(section: Section): Content[Section] {
  return content[section];
}
