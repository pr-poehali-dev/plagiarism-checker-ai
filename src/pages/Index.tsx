import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const CHECK_API_URL = 'https://functions.poehali.dev/de69dca0-423a-453c-8924-caa38d834c96';
const PDF_API_URL = 'https://functions.poehali.dev/e0bf7132-3c8a-4a86-b560-9cadd215f69c';

interface Match {
  source: string;
  similarity: number;
  excerpt: string;
}

interface UniquenessResult {
  uniqueness: number;
  words: number;
  characters: number;
  matches: Match[];
  ai_analysis: string;
}

export default function Index() {
  const [text, setText] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [result, setResult] = useState<UniquenessResult | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const { toast } = useToast();

  const handleCheck = async () => {
    if (text.length < 10) {
      toast({
        title: 'Ошибка',
        description: 'Текст слишком короткий (минимум 10 символов)',
        variant: 'destructive'
      });
      return;
    }

    setIsChecking(true);
    setResult(null);

    try {
      const response = await fetch(CHECK_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        throw new Error('Ошибка при проверке текста');
      }

      const data: UniquenessResult = await response.json();
      setResult(data);
      
      toast({
        title: 'Готово!',
        description: 'Анализ текста завершен',
      });
    } catch (error) {
      console.error('Error checking text:', error);
      toast({
        title: 'Ошибка',
        description: 'Не удалось проверить текст. Попробуйте позже.',
        variant: 'destructive'
      });
    } finally {
      setIsChecking(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!result) return;

    setIsDownloading(true);

    try {
      const response = await fetch(PDF_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          uniqueness: result.uniqueness,
          words: result.words,
          characters: result.characters,
          matches: result.matches,
          ai_analysis: result.ai_analysis
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('HTTP', response.status, ':', PDF_API_URL);
        console.error('Response:', errorText);
        throw new Error('Ошибка при генерации PDF');
      }

      const data = await response.json();
      
      if (!data.pdf) {
        console.error('No PDF in response:', data);
        throw new Error('Пустой ответ от сервера');
      }
      
      const linkSource = `data:application/pdf;base64,${data.pdf}`;
      const downloadLink = document.createElement('a');
      downloadLink.href = linkSource;
      downloadLink.download = data.filename;
      downloadLink.click();

      toast({
        title: 'Готово!',
        description: 'PDF отчет успешно скачан',
      });
    } catch (error) {
      console.error('Error generating PDF:', error);
      toast({
        title: 'Ошибка',
        description: 'Не удалось создать PDF отчет',
        variant: 'destructive'
      });
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center glow-effect">
              <Icon name="Scan" size={24} className="text-white" />
            </div>
            <h1 className="text-2xl font-heading font-bold gradient-text">PlagiatAI</h1>
          </div>
          <nav className="hidden md:flex gap-6">
            <a href="#home" className="text-muted-foreground hover:text-foreground transition-colors">Главная</a>
            <a href="#check" className="text-muted-foreground hover:text-foreground transition-colors">Проверка</a>
            <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">Тарифы</a>
            <a href="#faq" className="text-muted-foreground hover:text-foreground transition-colors">FAQ</a>
          </nav>
          <Button className="gradient-primary hover-scale">
            Войти
          </Button>
        </div>
      </header>

      <section id="home" className="py-20 px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-secondary/10 pointer-events-none" />
        <div className="container mx-auto max-w-6xl relative z-10">
          <div className="text-center animate-fade-in">
            <h2 className="text-5xl md:text-7xl font-heading font-bold mb-6">
              Проверка текста на <span className="gradient-text">уникальность</span>
            </h2>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Мощный ИИ-анализ с технологией DeepSeek для определения оригинальности вашего контента
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Button size="lg" className="gradient-primary hover-scale text-lg px-8" onClick={() => document.getElementById('check')?.scrollIntoView({ behavior: 'smooth' })}>
                Попробовать бесплатно
                <Icon name="ArrowRight" size={20} className="ml-2" />
              </Button>
              <Button size="lg" variant="outline" className="text-lg px-8">
                Узнать больше
              </Button>
            </div>
          </div>

          <div className="mt-20 grid md:grid-cols-3 gap-6">
            {[
              { icon: 'Brain', title: 'ИИ-анализ', desc: 'Технология DeepSeek для глубокой проверки' },
              { icon: 'Zap', title: 'Быстро', desc: 'Результат за несколько секунд' },
              { icon: 'FileCheck', title: 'PDF отчеты', desc: 'Детальные отчеты с источниками' }
            ].map((feature, i) => (
              <Card key={i} className="p-6 hover-scale border-border bg-card/50 backdrop-blur">
                <div className="w-12 h-12 rounded-lg bg-gradient-primary flex items-center justify-center mb-4 glow-effect">
                  <Icon name={feature.icon as any} size={24} className="text-white" />
                </div>
                <h3 className="text-xl font-heading font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="check" className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4 gradient-text">Проверить текст</h2>
            <p className="text-muted-foreground">Вставьте текст и получите детальный анализ уникальности</p>
          </div>

          <Card className="p-8">
            <Textarea
              placeholder="Вставьте текст для проверки..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="min-h-[300px] mb-6 text-lg"
            />
            <div className="flex justify-between items-center flex-wrap gap-4">
              <div className="text-sm text-muted-foreground">
                {text.split(' ').filter(w => w).length} слов • {text.length} символов
              </div>
              <Button 
                onClick={handleCheck} 
                disabled={!text || isChecking}
                className="gradient-primary hover-scale"
                size="lg"
              >
                {isChecking ? (
                  <>
                    <Icon name="Loader2" className="mr-2 animate-spin" size={20} />
                    Проверяем...
                  </>
                ) : (
                  <>
                    Проверить текст
                    <Icon name="Search" className="ml-2" size={20} />
                  </>
                )}
              </Button>
            </div>
          </Card>

          {result && (
            <Card className="p-8 mt-8 animate-fade-in">
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-gradient-primary mb-4 glow-effect">
                  <span className="text-5xl font-heading font-bold text-white">{result.uniqueness.toFixed(1)}%</span>
                </div>
                <h3 className="text-2xl font-heading font-bold mb-2">Уникальность текста</h3>
                <p className="text-muted-foreground">{result.ai_analysis}</p>
              </div>

              <div className="grid md:grid-cols-3 gap-4 mb-8">
                <Card className="p-4 bg-muted/30">
                  <div className="flex items-center gap-3">
                    <Icon name="FileText" size={24} className="text-primary" />
                    <div>
                      <div className="text-2xl font-bold">{result.words}</div>
                      <div className="text-sm text-muted-foreground">Слов</div>
                    </div>
                  </div>
                </Card>
                <Card className="p-4 bg-muted/30">
                  <div className="flex items-center gap-3">
                    <Icon name="Hash" size={24} className="text-secondary" />
                    <div>
                      <div className="text-2xl font-bold">{result.characters}</div>
                      <div className="text-sm text-muted-foreground">Символов</div>
                    </div>
                  </div>
                </Card>
                <Card className="p-4 bg-muted/30">
                  <div className="flex items-center gap-3">
                    <Icon name="Link" size={24} className="text-destructive" />
                    <div>
                      <div className="text-2xl font-bold">{result.matches.length}</div>
                      <div className="text-sm text-muted-foreground">Совпадений</div>
                    </div>
                  </div>
                </Card>
              </div>

              <div className="space-y-4 mb-8">
                <h4 className="font-heading font-semibold text-lg">Найденные совпадения:</h4>
                {result.matches.map((match: any, i: number) => (
                  <Card key={i} className="p-4 bg-muted/30">
                    <div className="flex items-start gap-4">
                      <Icon name="AlertCircle" size={20} className="text-destructive mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                          <a href={`https://${match.source}`} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline font-medium">
                            {match.source}
                          </a>
                          <span className="text-sm text-muted-foreground">{match.similarity}% совпадение</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{match.excerpt}</p>
                        <Progress value={match.similarity} className="mt-2 h-1" />
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              <div className="flex gap-4 flex-wrap">
                <Button 
                  className="gradient-primary flex-1 min-w-[200px]" 
                  size="lg"
                  onClick={handleDownloadPDF}
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <>
                      <Icon name="Loader2" className="mr-2 animate-spin" size={20} />
                      Создаем PDF...
                    </>
                  ) : (
                    <>
                      <Icon name="Download" size={20} className="mr-2" />
                      Скачать PDF отчет
                    </>
                  )}
                </Button>
                <Button variant="outline" size="lg">
                  <Icon name="Share2" size={20} className="mr-2" />
                  Поделиться
                </Button>
              </div>
            </Card>
          )}
        </div>
      </section>

      <section id="pricing" className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4 gradient-text">Тарифные планы</h2>
            <p className="text-muted-foreground">Выберите подходящий план для ваших задач</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { name: 'Базовый', price: '0', checks: '5', features: ['5 проверок в день', 'До 5000 символов', 'Базовый отчет'] },
              { name: 'Профи', price: '990', checks: '100', features: ['100 проверок в день', 'До 50000 символов', 'PDF отчеты', 'История проверок', 'API доступ'], popular: true },
              { name: 'Бизнес', price: '2990', checks: '∞', features: ['Безлимитные проверки', 'Без ограничений', 'Все возможности Профи', 'Приоритетная поддержка', 'Белый label'] }
            ].map((plan, i) => (
              <Card key={i} className={`p-8 relative ${plan.popular ? 'border-primary shadow-2xl md:scale-105' : ''}`}>
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-primary text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Популярный
                  </div>
                )}
                <h3 className="text-2xl font-heading font-bold mb-2">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-5xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground ml-2">₽/мес</span>
                </div>
                <div className="space-y-3 mb-8">
                  {plan.features.map((feature, j) => (
                    <div key={j} className="flex items-center gap-2">
                      <Icon name="Check" size={20} className="text-primary flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
                <Button className={plan.popular ? 'gradient-primary w-full' : 'w-full'} variant={plan.popular ? 'default' : 'outline'}>
                  Выбрать план
                </Button>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="faq" className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-3xl">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4 gradient-text">Часто задаваемые вопросы</h2>
          </div>

          <Accordion type="single" collapsible className="space-y-4">
            {[
              { q: 'Как работает проверка на уникальность?', a: 'Мы используем передовую ИИ-модель DeepSeek от SambaNova для анализа текста и сравнения с миллиардами документов в интернете.' },
              { q: 'Сколько времени занимает проверка?', a: 'Обычно проверка занимает от 5 до 30 секунд в зависимости от размера текста.' },
              { q: 'Можно ли скачать отчет?', a: 'Да, все пользователи могут скачать детальный PDF отчет с результатами проверки и списком найденных совпадений.' },
              { q: 'Есть ли API для интеграции?', a: 'Да, в тарифах Профи и Бизнес доступен API для интеграции с вашими системами.' },
              { q: 'Какие языки поддерживаются?', a: 'Сервис поддерживает русский, английский и еще более 50 языков для проверки уникальности.' }
            ].map((item, i) => (
              <AccordionItem key={i} value={`item-${i}`} className="border border-border rounded-lg px-6 bg-card">
                <AccordionTrigger className="text-left font-semibold hover:no-underline">
                  {item.q}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  {item.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      <footer className="border-t border-border py-12 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center">
                  <Icon name="Scan" size={18} className="text-white" />
                </div>
                <span className="font-heading font-bold text-lg">PlagiatAI</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Современный сервис проверки уникальности текстов с использованием ИИ
              </p>
            </div>
            <div>
              <h4 className="font-heading font-semibold mb-4">Продукт</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground transition-colors">Возможности</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Тарифы</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">API</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-heading font-semibold mb-4">Ресурсы</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground transition-colors">Документация</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">FAQ</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Поддержка</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-heading font-semibold mb-4">Контакты</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <Icon name="Mail" size={16} />
                  info@plagiatai.ru
                </li>
                <li className="flex items-center gap-2">
                  <Icon name="MessageCircle" size={16} />
                  Telegram
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">© 2024 PlagiatAI. Все права защищены.</p>
            <div className="flex gap-4 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors">Политика конфиденциальности</a>
              <a href="#" className="hover:text-foreground transition-colors">Условия использования</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}