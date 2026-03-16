interface MoodResult {
  genres: number[];
  sortBy: string;
  keywords: string;
  minRating: number;
  label: string;
}

interface MoodRule {
  patterns: RegExp[];
  genres: number[];
  sortBy?: string;
  keywords?: string;
  minRating?: number;
  label: string;
}

// TMDb genre IDs
// 28=Action, 12=Adventure, 16=Animation, 35=Comedy, 80=Crime,
// 99=Documentary, 18=Drama, 10751=Family, 14=Fantasy, 36=History,
// 27=Horror, 10402=Music, 9648=Mystery, 10749=Romance,
// 878=SF, 53=Thriller, 10752=War, 37=Western

const moodRules: MoodRule[] = [
  {
    patterns: [/泣[きけこい]/, /泣ける/, /涙/, /感動/, /号泣/, /ウルウル/, /じーん/],
    genres: [18, 10749],
    minRating: 7,
    sortBy: "vote_average.desc",
    label: "感動・涙の映画",
  },
  {
    patterns: [/笑[いえおう]/, /笑える/, /コメディ/, /おもしろ/, /面白/, /爆笑/, /ギャグ/, /くだらな/],
    genres: [35],
    label: "笑えるコメディ",
  },
  {
    patterns: [/怖[いけ]/, /ホラー/, /恐怖/, /ゾンビ/, /心霊/, /おばけ/, /幽霊/, /ゾッと/],
    genres: [27],
    label: "ホラー・恐怖映画",
  },
  {
    patterns: [/アクション/, /スカッと/, /爽快/, /バトル/, /格闘/, /戦闘/, /ドンパチ/, /暴れ/],
    genres: [28],
    label: "爽快アクション",
  },
  {
    patterns: [/恋愛/, /ロマンス/, /恋/, /ラブ/, /キュン/, /胸キュン/, /甘い/, /ときめ/],
    genres: [10749],
    label: "恋愛・ロマンス",
  },
  {
    patterns: [/SF/, /エスエフ/, /未来/, /宇宙/, /ロボット/, /AI/, /サイバー/, /近未来/],
    genres: [878],
    label: "SF・サイエンスフィクション",
  },
  {
    patterns: [/ファンタジー/, /魔法/, /異世界/, /ドラゴン/, /冒険/, /アドベンチャー/],
    genres: [14, 12],
    label: "ファンタジー・冒険",
  },
  {
    patterns: [/サスペンス/, /ハラハラ/, /ドキドキ/, /スリル/, /スリラー/, /緊張/, /手に汗/],
    genres: [53],
    label: "サスペンス・スリラー",
  },
  {
    patterns: [/ミステリー/, /謎/, /推理/, /トリック/, /犯人/, /探偵/, /事件/],
    genres: [9648, 80],
    label: "ミステリー・推理",
  },
  {
    patterns: [/アニメ/, /ジブリ/, /ピクサー/, /ディズニー/, /animated/i],
    genres: [16],
    label: "アニメーション",
  },
  {
    patterns: [/家族/, /子供/, /こども/, /ファミリー/, /親子/, /ほのぼの/, /ほっこり/],
    genres: [10751, 16],
    label: "ファミリー向け",
  },
  {
    patterns: [/戦争/, /歴史/, /実話/, /ノンフィクション/, /時代劇/, /史実/],
    genres: [10752, 36],
    label: "歴史・戦争",
  },
  {
    patterns: [/音楽/, /ミュージカル/, /バンド/, /歌/, /ライブ/, /ロック/, /ヒップホップ/],
    genres: [10402],
    label: "音楽映画",
  },
  {
    patterns: [/犯罪/, /クライム/, /マフィア/, /ギャング/, /ヤクザ/, /裏社会/, /強盗/],
    genres: [80, 53],
    label: "犯罪・クライム",
  },
  {
    patterns: [/頭.*空/, /何も考え/, /ぼーっと/, /リラックス/, /のんびり/, /気楽/, /まったり/],
    genres: [35, 16],
    label: "気楽に楽しめる映画",
  },
  {
    patterns: [/考えさせ/, /深い/, /哲学/, /重い/, /社会/, /人生/, /メッセージ/],
    genres: [18],
    minRating: 7.5,
    sortBy: "vote_average.desc",
    label: "考えさせられる名作",
  },
  {
    patterns: [/デート/, /カップル/, /二人/, /彼[女氏]/, /一緒に/],
    genres: [35, 10749],
    minRating: 6.5,
    label: "デートにぴったり",
  },
  {
    patterns: [/名作/, /傑作/, /神映画/, /最高/, /間違いない/, /ハズレな/, /鉄板/],
    genres: [],
    minRating: 8,
    sortBy: "vote_average.desc",
    label: "間違いない名作",
  },
  {
    patterns: [/話題/, /人気/, /流行/, /バズ/, /ヒット/, /興行/],
    genres: [],
    sortBy: "popularity.desc",
    label: "今話題の映画",
  },
];

const defaultResult: MoodResult = {
  genres: [],
  sortBy: "popularity.desc",
  keywords: "",
  minRating: 0,
  label: "おすすめ映画",
};

export function analyzeMood(input: string): MoodResult {
  const trimmed = input.trim();
  if (!trimmed) return defaultResult;

  const matchedGenres: number[] = [];
  let bestSortBy = "popularity.desc";
  let bestMinRating = 0;
  const labels: string[] = [];
  let matched = false;

  for (const rule of moodRules) {
    const isMatch = rule.patterns.some((p) => p.test(trimmed));
    if (isMatch) {
      matched = true;
      matchedGenres.push(...rule.genres);
      if (rule.sortBy) bestSortBy = rule.sortBy;
      if (rule.minRating && rule.minRating > bestMinRating) bestMinRating = rule.minRating;
      labels.push(rule.label);
    }
  }

  if (!matched) {
    return {
      ...defaultResult,
      keywords: trimmed,
      label: `「${trimmed}」に関連する映画`,
    };
  }

  // Deduplicate genres
  const uniqueGenres = [...new Set(matchedGenres)];

  return {
    genres: uniqueGenres,
    sortBy: bestSortBy,
    keywords: "",
    minRating: bestMinRating,
    label: labels.join(" × "),
  };
}

export const moodSuggestions = [
  "泣きたい",
  "笑いたい",
  "スカッとしたい",
  "怖い映画",
  "頭を空っぽにしたい",
  "デートで観たい",
  "考えさせられる映画",
  "ハラハラしたい",
  "名作が観たい",
  "アニメ",
  "恋愛もの",
  "SF・宇宙",
];
