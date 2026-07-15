export type Ticker = {
  symbol: string;
  name?: string;
  market: "A股" | "港股" | "美股" | "加密" | "产业链";
};

export type Opportunity = {
  id: string;
  title: string;
  summary: string;
  thesis: string;
  impact: "利好" | "利空" | "中性" | "待验证";
  confidence: "高" | "中" | "低";
  horizon: "短期" | "中期" | "长期";
  tickers: Ticker[];
  risk: string;
  source: string;
  sourceUrl: string;
  author: string;
  publishedAt?: string;
};

export type Category = {
  key: string;
  name: string;
  description: string;
  items: Opportunity[];
};

export type DailyBriefing = {
  date: string;
  generatedAt: string;
  status?: "live" | "preview";
  title: string;
  summary: string;
  marketPulse: string;
  stats: {
    sources: number;
    posts: number;
    opportunities: number;
    tickers: number;
  };
  categories: Category[];
};

export type NewsChannelKey = "ai" | "government" | "wallstreet" | "supply-chain" | "microcap";
export type NewsMarket = "美股" | "韩股" | "全球";

export type NewsItem = {
  id: string;
  channel: NewsChannelKey;
  title: string;
  summary: string;
  url: string;
  source: string;
  publishedAt: string;
  market: NewsMarket;
  sentiment: "偏多" | "偏空" | "中性";
  symbols: string[];
  sourceType: "官网" | "监管" | "X";
};
