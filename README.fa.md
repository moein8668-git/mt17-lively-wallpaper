# mt17 — راهنمای کامل والپیپر Lively

[English](README.md) | **فارسی**

والپیپر زنده برای [Lively Wallpaper](https://github.com/rocksdanister/lively) با ویژوالایزر واکنش‌گر به موسیقی، اطلاعات آهنگ در حال پخش، آب‌وهوا، ساعت، آمار سیستم، سرعت شبکه و اپ همراه **Preset Manager** برای ذخیره تم‌ها و اجرای **اسلایدشو خودکار پریست**.

---

## درباره این پروژه

**mt17** یک والپیپر سفارشی HTML/JS است که برای موتور WebView2 لایولی بهینه شده و از قابلیت‌های داخلی لایولی برای صدا، اطلاعات سیستم، متادیتای آهنگ در حال پخش و رویداد توقف استفاده می‌کند.

این پروژه با **[ChatGPT](https://chat.openai.com) و [Cursor](https://cursor.com)** به‌صورت vibe-code ساخته شده — طراحی، دیباگ و توسعه در جلسات کمک‌شده با هوش مصنوعی. ممکن است جاهایی ناهموار باشد؛ اگر چیزی در سیستم شما خراب شد، گزارش دهید.

**برای خود والپیپر به Python نیاز ندارید.** Python فقط برای Preset Manager اختیاری است.

---

## آنچه روی دسکتاپ می‌بینید

| قابلیت | توضیح |
|--------|--------|
| **پس‌زمینه متحرک** | ویدیوی حلقه‌ای از `media/` (اختیاری) |
| **پس‌زمینه ثابت** | تصویر از `images/` زیر لایه ویدیو |
| **ویژوالایزر موسیقی** | موج واکنش‌گر به صدا (صاف یا مربعی)، درخشش اختیاری |
| **آهنگ در حال پخش** | عنوان، هنرمند، کاور آلبوم از سشن رسانه ویندوز |
| **آب‌وهوا** | OpenWeather — دما، توضیح، دمای احساسی / رطوبت / باد (اختیاری) |
| **ساعت** | زمان، ردیف روزهای هفته، تاریخ — ۱۲ یا ۲۴ ساعته |
| **مصرف سیستم** | درصد CPU، RAM، GPU |
| **سرعت شبکه** | دانلود / آپلود (Mb/s یا MB/s)، پایین راست |
| **اسلایدشو پریست** | چرخش خودکار پریست‌های ذخیره‌شده با cross-fade (تنظیم در **رابط وب** Preset Manager) |

وقتی لایولی والپیپر را **متوقف** می‌کند (صرفه‌جویی باتری / حالت تمرکز)، پس‌زمینه متحرک و به‌روزرسانی ساعت کند می‌شود؛ ویژوالایزر تا از سرگیری، کار سنگین انجام نمی‌دهد.

---

## چیزهایی که لازم دارید

| مورد | برای | جزئیات |
|------|--------|--------|
| **ویندوز 10/11** | والپیپر | |
| **Lively Wallpaper** | والپیپر | [Microsoft Store](https://apps.microsoft.com/detail/9ntm2qc6qws7) یا [GitHub releases](https://github.com/rocksdanister/lively/releases) |
| **کلید API OpenWeather** | فقط آب‌وهوا | کلید رایگان از [openweathermap.org/api](https://openweathermap.org/api) — در Customize لایولی وارد کنید |
| **Python 3.10+** | فقط Preset Manager | [python.org](https://www.python.org/downloads/) — گزینه **Add Python to PATH** را فعال کنید |
| **Flask** | رابط وب (پیشنهادی) | نصب از `preset-manager/requirements.txt` |

---

## بخش ۱ — نصب والپیپر در Lively

### ۱. پوشه والپیپر را آماده کنید

به کل پوشه پروژه نیاز دارید (عنوان **mt17** در `LivelyInfo.json`). حداقل باید شامل این موارد باشد:

- `index.html`، `LivelyInfo.json`، `LivelyProperties.json`
- `js/`، `styles/`، `media/`، `images/`، `fonts/`، `presets/`، `res/` (و اختیاری `preset-manager/`)

می‌توانید از هر پوشه‌ای توسعه دهید (مثلاً `D:\Live background\`) یا در کتابخانه لایولی کپی کنید.

### ۲. افزودن به Lively

**روش الف — از داخل Lively (پیشنهادی)**

1. **Lively Wallpaper** را باز کنید.
2. **+** → **Add wallpaper** / **Local file**.
3. **پوشه** حاوی `LivelyInfo.json` را انتخاب کنید (نه فقط `index.html`).
4. **mt17** را روی مانیتور(های) دلخواه تنظیم کنید.

**روش ب — کپی در کتابخانه Lively**

کل پوشه را اینجا کپی کنید:

```text
%LOCALAPPDATA%\Packages\12030rocksdanister.LivelyWallpaper_97hta09mmv6hy\LocalCache\Local\Lively Wallpaper\Library\wallpapers\
```

لایولی یک زیرپوشه تصادفی می‌سازد (می‌توانید خودتان هم نام بگذارید، مثلاً `mt17cus2igg`). لایولی را ری‌استارت کنید یا کتابخانه را رفرش کنید، سپس **mt17** را اعمال کنید.

### ۳. بررسی عملکرد

باید پس‌زمینه و ویجت‌ها را ببینید. برای تست ویژوالایزر موسیقی پخش کنید. راست‌کلیک روی والپیپر در Lively → **Customize** برای تنظیمات.

### ۴. پوشه توسعه در مقابل نسخه نصب‌شده

اگر در **پوشه توسعه** ویرایش می‌کنید ولی Lively یک **کپی** زیر `Library\wallpapers\...` اجرا می‌کند، تغییرات تا کپی فایل‌های به‌روز در پوشه نصب‌شده یا افزودن دوباره پوشه توسعه در Lively دیده نمی‌شود.

**Customize** لایولی تنظیمات را از **SaveData** می‌خواند، نه همیشه از فایل ریشه والپیپر:

```text
Library\SaveData\wpdata\{wallpaper-id}\{monitor}\LivelyProperties.json
```

بعد از به‌روزرسانی `LivelyProperties.json` در پروژه، در پایین Customize روی **Reload settings from LivelyProperties.json** بزنید (یا والپیپر را دوباره اضافه کنید).

---

## بخش ۲ — Customize لایولی (مرجع کامل)

**Customize** را برای **mt17** در Lively باز کنید. همه کنترل‌ها در `LivelyProperties.json` تعریف شده‌اند.

### فونت‌ها (بالای Customize)

پنج **منوی کشویی پوشه** (مرور پوشه `fonts/`):

| کنترل | کاربرد |
|-------|--------|
| Song title font | عنوان آهنگ در حال پخش |
| Artist name font | نام هنرمند |
| Weather font | پنل آب‌وهوا |
| System usage font | CPU/RAM/GPU **و** سرعت شبکه |
| Clock font | زمان، روزهای هفته، تاریخ |

فایل‌های `.ttf`، `.otf` یا `.woff` را در `fonts/` بگذارید و در Customize یا پنل Customize لایولی انتخاب کنید.

### پس‌زمینه

| کنترل | کاربرد |
|-------|--------|
| Animated background | ویدیو از `media/` |
| Static wallpaper | تصویر از `images/` |
| Show animated background | روشن/خاموش لایه ویدیو |

### رسانه و ویژوالایزر

| کنترل | کاربرد |
|-------|--------|
| Show album art / song title / artist | بلوک آهنگ در حال پخش |
| Album art size, title/artist font sizes & colors | استایل رسانه |
| Media block position | `contentTop` / `contentLeft` |
| Song title character limit | کوتاه کردن عنوان‌های بلند |
| Visualizer color, size, position, margin | ظاهر موج |
| Square wave / Visualizer glow | شکل موج و درخشش |
| Visualizer fill color | ناحیه زیر موج |

### آب‌وهوا

| کنترل | کاربرد |
|-------|--------|
| OpenWeather API key, city or lat/lon, units | منبع داده |
| Refresh interval | فاصله به‌روزرسانی |
| Position, colors, icon size | چیدمان و استایل |
| Feels-like / humidity / wind | خط اضافی اختیاری |

اگر کلید API نباشد یا درخواست خطا بدهد، پنل آب‌وهوا پیام خطا نشان می‌دهد (نه سکوت).

### مصرف سیستم و شبکه

| کنترل | کاربرد |
|-------|--------|
| Show CPU / GPU / RAM | روشن/خاموش جداگانه |
| System panel position, colors, font, decimals | استایل |
| Show network speed | سرعت ↓/↑ پایین راست |
| Network position, colors, background, font size | استایل |
| Network speed unit | **Mb/s** (مگابیت) یا **MB/s** (مگابایت) |

### ساعت

| کنترل | کاربرد |
|-------|--------|
| Show clock / show all weekdays | نمایش |
| 24-hour clock | خاموش = ۱۲ ساعته با AM/PM |
| Colors, positions, font sizes, gaps | کنترل کامل چیدمان |

### نکته‌ها

- **پریست در Customize نیست** — تعداد زیاد کنترل باعث کرش می‌شد؛ از Preset Manager استفاده کنید.
- **Apply دستی از Preset Manager** در SaveData می‌نویسد و راه مطمئن برای ثابت ماندن ظاهر بعد از ری‌استارت است.
- **اسلایدشو** در هر اسلاید SaveData نمی‌نویسد — بخش ۴ را ببینید.
- **محدوده اسلایدرها** برای رزولوشن‌های بزرگ گسترش یافته: موقعیت‌ها می‌توانند منفی یا بالای ۱۰۰۰px باشند؛ لنگر ساعت −۵۰ تا ۱۵۰٪.

---

## بخش ۳ — Preset Manager

Preset Manager یک **اپ همراه Python** کوچک است که:

- ظاهر فعلی والپیپر زنده را به فایل `.preset.json` **ذخیره** می‌کند
- پریست ذخیره‌شده را روی والپیپر در حال اجرا **اعمال** می‌کند
- با Apply/Save در **SaveData لایولی** می‌نویسد تا تنظیمات بعد از ری‌استارت بماند (به ازای هر مانیتور)
- پیکربندی **اسلایدشو پریست** را انجام می‌دهد (فقط رابط وب)
- **بسته ZIP قابل حمل** (پریست + media/fonts/images) را صادر/وارد می‌کند (فقط رابط وب)

پریست‌ها اینجا ذخیره می‌شوند:

```text
{پوشه والپیپر}/presets/*.preset.json
{پوشه والپیپر}/presets/manifest.json
{پوشه والپیپر}/presets/slideshow.json
```

**پوشه والپیپر** خودکار از محل `preset-manager/` تشخیص داده می‌شود (همان جایی که `LivelyInfo.json` است). مهم نیست پروژه کجا باشد — لایولی باید به **همان پوشه** اشاره کند.

### اجرای برنامه

1. پوشه `preset-manager/` داخل والپیپر را باز کنید.
2. روی **`start.bat`** دوبار کلیک کنید.

| Flask نصب باشد | Flask نصب **نباشد** |
|----------------|---------------------|
| **رابط وب** در http://127.0.0.1:8767 باز می‌شود | **پنجره دسکتاپ (Tk)** |

نصب Flask (پیشنهادی):

```bat
python -m pip install -r preset-manager/requirements.txt
```

اجبار به یک رابط:

```bat
python main.py --web
python main.py --tk
```

### تنظیم اولیه

1. **mt17** در Lively فعال باشد (از **همان پوشه**ای که `preset-manager/` داخلش است).
2. Preset Manager را اجرا کنید — خط **Wallpaper folder (auto from script):** مسیر تشخیص‌داده‌شده را نشان می‌دهد.
3. در **Settings** (وب: بالا راست؛ Tk: دکمه Settings):
   - **Auto-detected wallpaper folder** — والد `preset-manager/`؛ معمولاً تغییر ندهید.
   - **Override wallpaper folder** — اختیاری، فقط پیشرفته.
   - **Monitor** — SaveData کدام مانیتور به‌روز شود (رابط وب: منوی کشویی صفحه اصلی).
4. Save → در `preset-manager/config.json` ذخیره می‌شود (مانیتور + override اختیاری).

Apply/Save نیاز دارد والپیپر **زنده** در Lively باشد. برنامه از طریق `presets/_command.json` (هر ~۱.۵ ثانیه) و API روی پورت **8766** با والپیپر صحبت می‌کند.
اگر پورت API را در تنظیمات تغییر دادید، یک‌بار والپیپر را Reload کنید تا `presets/_preset-api.json` را دوباره بخواند. اگر SaveData در دسترس نباشد، برنامه صریحاً اعلام می‌کند که پریست محلی ذخیره شده اما برای راه‌اندازی مجدد پایدار نشده است.

---

## بخش ۴ — کار با پریست‌ها

### روال پایه

1. ظاهر را در **Lively Customize** تنظیم کنید (اختیاری).
2. در Preset Manager یک **نام پریست** بنویسید.
3. **Save current look** — چند ثانیه صبر تا والپیپر وضعیت را ثبت کند.
4. بعداً: پریست را انتخاب کنید → **Apply to wallpaper**.

Apply فوراً دسکتاپ را به‌روز می‌کند **و** مقادیر متناظر را در SaveData لایولی برای مانیتور انتخاب‌شده می‌نویسد.

### اسلایدشو پریست (فقط رابط وب)

چرخش پریست‌ها مثل اسلایدشو پس‌زمینه ویندوز:

1. **۲+ پریست** با تفاوت واضح بسازید.
2. در بخش **Slideshow** رابط وب:
   - **Add selected preset** برای ساخت پلی‌لیست (با **Up/Down** مرتب کنید).
   - **Interval** (دقیقه؛ حداقل ۳۰ ثانیه).
   - **Cross-fade** (ثانیه؛ `0` = فوری، پیش‌فرض `1.2`).
   - **Order**: sequential، random یا shuffle (بدون تکرار تا پخش همه).
   - **Enable preset slideshow** را تیک بزنید.
3. **Save slideshow** را بزنید.

| موضوع | رفتار |
|-------|--------|
| تایمر را چه کسی اجرا می‌کند | **والپیپر** فایل `presets/slideshow.json` را می‌خواند |
| Preset Manager باید باز بماند؟ | **خیر** — فقط برای ویرایش تنظیمات اسلایدشو لازم است |
| SaveData در هر اسلاید | **خیر** — فقط بصری؛ آخرین اسلاید می‌ماند تا دستی Apply کنید |
| بعد از ری‌استارت | اگر `enabled: true` در `slideshow.json` باشد، ادامه می‌یابد |
| Apply دستی | اسلایدشو متوقف می‌شود؛ دوباره با تیک **Enable** ذخیره کنید |
| Cross-fade | محو لایه دوگانه پس‌زمینه + محو UI (فقط اسلایدشو؛ Apply دستی فوری است) |

### بسته ZIP قابل حمل (فقط رابط وب)

اشتراک تم کامل — پریست **به‌همراه** media، images و fonts.

**ZIP تک پریست**

1. پریست را انتخاب کنید → **Download preset ZIP**.
2. گزینه‌های حریم خصوصی هنگام export (پیش‌فرض برای اشتراک فعال):
   - **Blank OpenWeather API key**
   - **Randomize location**
3. روی PC دیگر: **Upload preset ZIP** — فایل‌ها در `media/`، `images/`، `fonts/` نصب می‌شوند.
4. نام از `package.json` → `presetFile` (مثلاً `gojo-1.preset.json` → **gojo-1**).
5. پریست را انتخاب کنید → **Apply to wallpaper**.

**ZIP پشتیبان کامل**

- **Download full backup ZIP** — همه پریست‌ها + `slideshow.json` + دارایی‌ها
- **Upload full backup ZIP** — جایگزینی پریست‌ها + بازیابی اسلایدشو (با تأیید)

JSON فقط تنظیمات است (بدون media/fonts).

### مقایسه رابط وب و Tk دسکتاپ

| قابلیت | رابط وب (Flask) | Tk دسکتاپ (`--tk`) |
|--------|:---------------:|:------------------:|
| Apply preset | بله | بله |
| Save current look | بله | بله |
| Rename / Delete / Duplicate | بله | بله |
| پشتیبان محلی / بازیابی آخرین | بله | بله |
| انتخاب مانیتور | بله (صفحه اصلی) | بله (Settings) |
| تغییر مسیر پوشه والپیپر | بله | بله |
| **اسلایدشو پریست** | **بله** | **خیر** |
| **تنظیمات Cross-fade** | **بله** | **خیر** |
| **View settings** (نمایش خوانا پریست) | **بله** | **خیر** |
| **دانلود / آپلود JSON تک پریست** | **بله** | **خیر** |
| **دانلود / آپلود ZIP تک پریست** | **بله** | **خیر** |
| **دانلود / آپلود JSON پشتیبان کامل** | **بله** | **خیر** |
| **دانلود / آپلود ZIP پشتیبان کامل** | **بله** | **خیر** |
| تصویر بندانگشتی والپیپر در هدر | بله | خیر |

**پیشنهاد:** Flask را نصب کنید و از **رابط وب** برای تجربه کامل استفاده کنید. Tk فقط fallback ساده وقتی Flask در دسترس نیست.

### همه عملیات Preset Manager (رابط وب)

| عملیات | کار |
|--------|-----|
| **Apply to wallpaper** | بارگذاری پریست + به‌روز SaveData |
| **Save current look** | ثبت وضعیت زنده + به‌روز SaveData |
| **Rename / Delete / Duplicate** | مدیریت فایل پریست |
| **View settings** | فهرست خوانای مقادیر ذخیره‌شده |
| **Download preset JSON** | فقط تنظیمات (بدون دارایی) |
| **Upload preset JSON** | فقط تنظیمات |
| **Download preset ZIP** | پریست + media/fonts/images |
| **Upload preset ZIP** | ورود پریست + نصب دارایی‌ها |
| **Create local backup** | کپی `presets/` به `%LocalAppData%\Mt17PresetManager\backups\` |
| **Download backup JSON** | همه پریست‌ها + manifest (بدون دارایی) |
| **Upload backup JSON** | بازیابی از آن فایل |
| **Download full backup ZIP** | همه پریست‌ها + اسلایدشو + دارایی‌ها |
| **Upload full backup ZIP** | بازیابی کامل + دارایی‌ها |
| **Restore latest local backup** | بازیابی آخرین پوشه پشتیبان |
| **Save slideshow** | نوشتن `slideshow.json` |

### محل ذخیره فایل‌ها

| مورد | مسیر |
|------|------|
| پریست‌ها | `{پوشه والپیپر}/presets/*.preset.json` |
| تنظیمات اسلایدشو | `{پوشه والپیپر}/presets/slideshow.json` |
| پل ارتباطی | `{پوشه والپیپر}/presets/_command.json` (موقت) |
| پشتیبان محلی | `%LocalAppData%\Mt17PresetManager\backups\` |
| تنظیمات برنامه | `preset-manager/config.json` |
| SaveData لایولی (هر مانیتور) | `%LocalAppData%\...\Lively Wallpaper\Library\SaveData\wpdata\{id}\{monitor}\LivelyProperties.json` |

---

## بخش ۵ — ساختار پروژه

```text
mt17/
├── README.md / README.fa.md   ← راهنما (انگلیسی / فارسی)
├── index.html                 ← ورودی والپیپر
├── LivelyInfo.json            ← متادیتا و آرگومان‌های Lively
├── LivelyProperties.json      ← قالب پنل Customize
├── js/
│   └── script.js              ← منطق والپیپر + تایمر اسلایدشو
├── styles/
│   └── style.css
├── media/                     ← ویدیوهای پس‌زمینه (.webm, .mp4, …)
├── images/                    ← والپیپرهای ثابت
├── fonts/                     ← فونت‌های سفارشی برای Customize
├── res/                       ← کاور پیش‌فرض آلبوم و غیره
├── presets/
│   ├── manifest.json          ← فهرست پریست‌ها
│   ├── slideshow.json         ← تنظیمات اسلایدشو (رابط وب)
│   ├── _command.json          ← پل زمان اجرا (ساخته‌شده توسط Preset Manager)
│   └── *.preset.json          ← تم‌های ذخیره‌شده
└── preset-manager/
    ├── start.bat              ← اجرای Preset Manager
    ├── main.py                ← لانچر وب یا Tk
    ├── webui.py               ← رابط وب Flask (پورت 8767)
    ├── server.py              ← API HTTP (پورت 8766)
    ├── preset_store.py        ← پریست و اسلایدشو روی دیسک
    ├── preset_package.py      ← صادر/وارد ZIP + بسته‌بندی دارایی‌ها
    ├── lively_properties.py   ← نگاشت همگام‌سازی SaveData
    ├── lively_paths.py        ← مسیر از محل اسکریپت + یافتن SaveData
    ├── preset_labels.py       ← برچسب‌های خوانا برای View settings
    ├── config.py              ← پیش‌فرض‌ها و مسیر پشتیبان
    ├── requirements.txt       ← وابستگی Python (Flask)
    ├── README.md              ← ارجاع کوتاه به راهنمای اصلی
    ├── config.json            ← مسیرها و مانیتور شما (با Save ساخته می‌شود)
    ├── templates/
    │   └── index.html         ← صفحه رابط وب
    └── static/
        ├── app.js             ← منطق رابط وب
        └── app.css            ← استایل رابط وب
```

### آرگومان‌های Lively (در `LivelyInfo.json`)

```text
--system-nowplaying --audio --system-information --pause-event true
```

این‌ها متادیتای آهنگ در حال پخش، داده ویژوالایزر صدا، آمار CPU/GPU/RAM/شبکه و اعلان توقف را فعال می‌کنند.

---

## رفع مشکل

### والپیپر در Lively دیده نمی‌شود

- **پوشه** حاوی `LivelyInfo.json` را انتخاب کنید، نه یک فایل تکی.
- بعد از کپی دستی، Lively را ری‌استارت کنید.

### Customize خالی است، کرش می‌کند یا انتخابگر فونت پوشه اشتباه باز می‌کند

- در Customize روی **Reload settings from LivelyProperties.json** بزنید.
- انتخابگر فونت‌ها **بالای** Customize است؛ `folder: "fonts"` در SaveData بماند (reload ورودی‌های خراب را درست می‌کند).

### آب‌وهوا خطا نشان می‌دهد

- کلید معتبر **OpenWeather API** در Customize وارد کنید.
- نام شهر یا lat/lon و اتصال اینترنت را بررسی کنید.

### Apply / Save کار نمی‌کند

1. **mt17** باید والپیپر فعال در Lively باشد.
2. Preset Manager باید در حال اجرا باشد (`start.bat`).
3. Lively باید از **همان پوشه**ای استفاده کند که *Wallpaper folder (auto from script)* نشان می‌دهد.
4. اگر **override** قدیمی در Settings است، آن را پاک کنید.
5. والپیپر را یک‌بار در Lively reload کنید.

### ZIP وارد شد ولی ظاهر درست نیست

1. مسیر **wallpaper folder** در پیام وضعیت را بررسی کنید.
2. بعد از import حتماً **Apply to wallpaper** بزنید.
3. برای پشتیبان کامل از **Upload full backup ZIP** استفاده کنید، نه upload تک پریست.
4. import مجدد همان ZIP، پریست با همان نام `presetFile` را بازنویسی می‌کند.

### اسلایدشو پریست عوض نمی‌شود

1. در `presets/slideshow.json` مقدار `"enabled": true` و `playlist` غیرخالی باشد.
2. حداقل فاصله **۳۰ ثانیه** است.
3. اسلایدشو در والپیپر اجرا می‌شود — اگر از کپی کتابخانه استفاده می‌کنید، `slideshow.json` را در پوشه **نصب‌شده** والپیپر ویرایش/کپی کنید.
4. بعد از **Apply** دستی، اسلایدشو را دوباره با تیک **Enable** ذخیره کنید.

### رابط وب باز نمی‌شود

```bat
python -m pip install -r preset-manager/requirements.txt
start.bat
```

یا Tk: `python main.py --tk` (قابلیت محدود — جدول بالا).

### Python پیدا نمی‌شود

Python را با **Add to PATH** دوباره نصب کنید، یا از ترمینالی اجرا کنید که `python --version` کار می‌کند.

### تغییرات در پوشه توسعه روی دسکتاپ دیده نمی‌شود

فایل‌های به‌روز را به `Library\wallpapers\{your-id}\` کپی کنید یا Lively را مستقیم به پوشه توسعه اشاره دهید.

---

## مرجع سریع

| کار | مراحل |
|-----|--------|
| افزودن والپیپر | Lively → Add → پوشه mt17 → Set as wallpaper |
| تغییر ظاهر | Lively → Customize |
| ذخیره تم (ماندگار) | Preset Manager → نام → **Save current look** |
| بارگذاری تم (ماندگار) | Preset Manager → انتخاب → **Apply to wallpaper** |
| چرخش خودکار تم‌ها | رابط وب → **Slideshow** → پلی‌لیست → Enable → Save |
| اشتراک پریست (با دارایی) | رابط وب → **Download preset ZIP** |
| ورود پریست اشتراکی | رابط وب → **Upload preset ZIP** → **Apply** |
| اجرای Preset Manager | `preset-manager/start.bat` |
| رابط کامل Preset Manager | نصب `preset-manager/requirements.txt` → رابط وب روی :8767 |

---

## اعتبار و مجوز

ساخته‌شده برای استفاده شخصی با **Lively Wallpaper**، **OpenWeather**، **GPT** و **Cursor**. رسانه والپیپر، فونت‌ها و دارایی‌های بسته‌شده مال شماست — `media/`، `images/` و `fonts/` را دلخواه عوض کنید.
