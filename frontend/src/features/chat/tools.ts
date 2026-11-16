/** Names people understand for the data a tool reads, from its `<domain>_<action>` name. */
const DOMAIN_LABELS: Record<string, string> = {
  finance: 'Tài chính',
  travel: 'Du lịch',
  food: 'Ẩm thực',
}

export function toolLabel(toolName: string): string {
  const domain = toolName.split('_')[0]
  return DOMAIN_LABELS[domain] ?? toolName
}
