const ROLE_LABELS: Record<string, string> = {
  user: "Пользователь",
  moderator: "Модератор",
  admin: "Администратор"
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Ожидает",
  ok: "Опубликовано",
  hidden: "Скрыто",
  blocked: "Заблокировано",
  deleted: "Удалено",
  approved_manual: "Одобрено модератором"
};

const VIOLATION_LABELS: Record<string, string> = {
  spam: "Спам",
  flood: "Флуд",
  duplicate: "Дубликат",
  stopword: "Стоп-слово",
  toxicity: "Токсичность",
  link: "Ссылка",
  admin_action: "Действие модератора",
  rule: "Сработало правило"
};

const CODE_LABELS: Record<string, string> = {
  blocked: "Сообщение заблокировано",
  n_a: "н/д",
  unauthorized: "Нет авторизации",
  user_not_found: "Пользователь не найден",
  user_blocked: "Пользователь временно заблокирован",
  shadow_ban_or_high_rating: "Сообщение скрыто из-за санкций по рейтингу",
  room_not_allowed: "Недопустимая комната",
  text_required: "Введите текст сообщения",
  text_too_long: "Сообщение слишком длинное",
  length_lt_2: "Слишком короткое сообщение",
  flood: "Слишком частая отправка сообщений",
  duplicate: "Повтор одного и того же сообщения",
  stopword: "Обнаружено запрещенное слово",
  link: "Обнаружена ссылка",
  too_many_links: "Слишком много ссылок",
  repeated_symbols: "Чрезмерные повторы символов",
  invalid_credentials: "Неверный логин или пароль",
  username_required: "Введите имя пользователя",
  username_invalid: "Некорректное имя пользователя",
  username_taken: "Имя пользователя уже занято",
  password_required: "Введите пароль",
  password_too_short: "Пароль слишком короткий",
  email_taken: "Email уже используется",
  register_failed: "Ошибка регистрации",
  login_failed: "Ошибка входа"
};

const RULE_LABELS: Record<string, string> = {
  auth: "Авторизация",
  room: "Проверка комнаты",
  validation: "Валидация",
  user_blocked: "Блокировка пользователя",
  link: "Проверка ссылок",
  flood: "Проверка флуда",
  duplicate: "Проверка дубликатов",
  stopword: "Проверка стоп-слов",
  too_many_links: "Лимит ссылок",
  repeated_symbols: "Повторы символов",
  length_lt_2: "Минимальная длина",
  score: "Оценка ML"
};

export function roleLabel(role?: string | null): string {
  if (!role) return "Неизвестно";
  return ROLE_LABELS[role] || role;
}

export function statusLabel(status?: string | null): string {
  if (!status) return "Неизвестно";
  return STATUS_LABELS[status] || status;
}

export function violationLabel(type?: string | null): string {
  if (!type) return "Неизвестно";
  return VIOLATION_LABELS[type] || type;
}

export function codeLabel(code?: string | null): string {
  if (!code) return "Причина не указана";
  return CODE_LABELS[code] || code;
}

export function ruleLabel(rule?: string | null): string {
  if (!rule) return "н/д";
  const values = rule
    .split(",")
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => RULE_LABELS[token] || CODE_LABELS[token] || token);
  return values.join(", ");
}

export function formatDecisionReason(reason?: string | null): string {
  if (!reason) return "Причина не указана";

  if (reason.startsWith("rule_block:")) {
    const codes = reason.replace("rule_block:", "");
    return `Блокировка по правилам: ${ruleLabel(codes)}`;
  }

  if (reason.startsWith("rule_warn:")) {
    const parts = reason.split(";");
    const warnPart = parts[0].replace("rule_warn:", "");
    const otherParts = parts.slice(1);
    const normalizedOther = otherParts
      .map((item) => item.trim())
      .filter(Boolean)
      .join("; ");
    return normalizedOther
      ? `Предупреждение: ${ruleLabel(warnPart)}; ${normalizedOther}`
      : `Предупреждение: ${ruleLabel(warnPart)}`;
  }

  if (reason.includes(";") || reason.startsWith("score:") || reason.startsWith("thresholds:")) {
    const parts = reason
      .split(";")
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => {
        if (item.startsWith("score:")) {
          return `Оценка: ${item.replace("score:", "")}`;
        }
        if (item.startsWith("thresholds:")) {
          return `Пороги: ${item.replace("thresholds:", "")}`;
        }
        return codeLabel(item);
      });
    return parts.join("; ");
  }

  return codeLabel(reason);
}

export function authErrorLabel(code?: string | null): string {
  return codeLabel(code);
}
