import { Button } from "antd";
import { setRequestLocale } from "next-intl/server";

import { pickContent } from "@/lib/content";

export default async function Home({
  params,
}: Readonly<{ params: Promise<{ locale: string }> }>) {
  const { locale } = await params;
  setRequestLocale(locale);
  const hero = pickContent("hero");

  return (
    <main className="landing-shell">
      <p className="eyebrow">{hero.eyebrow}</p>
      <h1>{hero.title}</h1>
      <p className="lede">{hero.description}</p>
      <Button type="primary" size="large">
        {hero.cta}
      </Button>
    </main>
  );
}
