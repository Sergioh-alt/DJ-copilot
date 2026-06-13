import { useState } from 'react';

interface Method {
  id: string;
  name: string;
  icon: string;
  description: string;
  steps: string[];
  tips: string;
  tags: string[];
}

export default function TransitionGuide() {
  const [selected, setSelected] = useState<Method | null>(null);

  const methods: Method[] = [
    {
      id: 'progressive_blend',
      name: 'Progressive Blend (Mezcla Progresiva)',
      icon: '🌊',
      description: 'La técnica estándar para House y Melodic Techno. Se trata de introducir la nueva canción muy lentamente usando los EQs.',
      steps: [
        'Carga el Track B y ajusta el BPM.',
        'Quita totalmente los bajos (Low) del Track B.',
        'Sube el fader del Track B al máximo.',
        'Introduce gradualmente los Medios y Agudos del Track B.',
        'En el compás 16 o 32, intercambia los bajos (quita el A, pon el B).',
        'Retira lentamente el Track A.'
      ],
      tips: 'Ideal para tracks con frases largas y atmósferas similares.',
      tags: ['House', 'Techno', 'Smooth']
    },
    {
      id: 'bass_swap',
      name: 'Bass Swap (Intercambio de Bajos)',
      icon: '🎚️',
      description: 'Una técnica dinámica para Techno y Tech-House. El cambio se siente instantáneo y energético.',
      steps: [
        'Introduce el Track B con los bajos a la mitad o quitados.',
        'Busca el final de una frase o un drop pequeño en el Track A.',
        'En el golpe del compás 1, gira rápidamente el Low de A a la izquierda y el de B a la derecha.',
        'La energía del bajo cambia de una canción a otra instantáneamente.'
      ],
      tips: 'Asegúrate de que los niveles de ganancia de ambos bajos sean iguales para no perder pegada.',
      tags: ['Techno', 'Energy', 'Precise']
    },
    {
      id: 'echo_out',
      name: 'Echo Out (Salida con Eco)',
      icon: '📡',
      description: 'Perfecta para cambiar radicalmente de BPM o de estilo (ej. de Techno a Reggaeton).',
      steps: [
        'Activa el efecto Echo en el Track A.',
        'Ajusta el tiempo del eco a 1/2 o 3/4 de tiempo.',
        'Gira la perilla de intensidad (Wet/Dry) y baja el fader de A rápidamente.',
        'Lanza el Track B inmediatamente en el primer tiempo.'
      ],
      tips: 'El eco rellena el silencio mientras lanzas la nueva canción.',
      tags: ['Utility', 'Creative', 'Style Change']
    },
    {
      id: 'filter_sweep',
      name: 'Filter Sweep (Barrido de Filtro)',
      icon: '🌀',
      description: 'Usa el filtro High Pass o Low Pass para crear tensión antes del cambio.',
      steps: [
        'Aplica un High Pass Filter al Track A durante los últimos 4 compases.',
        'Lanza el Track B con un filtro similar.',
        'Gira el filtro de B a la posición neutral mientras retiras A.',
        'El efecto de "lavado" oculta las diferencias de textura.'
      ],
      tips: 'No abuses del filtro o cansarás el oído de la audiencia.',
      tags: ['Electronic', 'Tension']
    },
    {
      id: 'cut',
      name: 'The Cut (El Corte Seco)',
      icon: '✂️',
      description: 'La técnica clásica del Hip-Hop y Reggaeton. Cambio instantáneo de una canción a otra.',
      steps: [
        'Alinea el primer tiempo (Downbeat) de ambas canciones.',
        'En el final de un estribillo o frase, mueve el crossfader de golpe de A a B.',
        'O baja el fader de A y sube el de B al mismo tiempo exacto.'
      ],
      tips: 'Requiere una sincronización perfecta y que ambas canciones tengan una energía similar.',
      tags: ['Reggaeton', 'Hip-Hop', 'Fast']
    }
  ];

  return (
    <div className="animate-in">
      <div className="view-header">
        <h2>📚 Guía de Transiciones</h2>
        <p>Aprende a ejecutar cada método de mezcla recomendado por la IA</p>
      </div>

      <div className="flex gap-24">
        {/* List */}
        <div style={{ flex: 1 }}>
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            {methods.map((m) => (
              <div 
                key={m.id} 
                className={`nav-item ${selected?.id === m.id ? 'active' : ''}`}
                style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', borderRadius: '0', cursor: 'pointer' }}
                onClick={() => setSelected(m)}
              >
                <span style={{ fontSize: '20px', marginRight: '12px' }}>{m.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '14px' }}>{m.name}</div>
                  <div className="flex gap-4 mt-4">
                    {m.tags.map(t => <span key={t} className="text-muted" style={{ fontSize: '10px', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>{t}</span>)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Details */}
        <div style={{ flex: 1.5 }}>
          {selected ? (
            <div className="card animate-in">
              <div className="flex items-center gap-16 mb-16">
                <span style={{ fontSize: '48px' }}>{selected.icon}</span>
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: 800 }}>{selected.name}</h3>
                  <p className="text-muted">{selected.description}</p>
                </div>
              </div>

              <div style={{ background: 'var(--bg-tertiary)', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
                <h4 style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', color: 'var(--accent-cyan)', marginBottom: '12px' }}>
                  Pasos a seguir:
                </h4>
                <ol style={{ paddingLeft: '20px', color: 'var(--text-main)', fontSize: '14px' }}>
                  {selected.steps.map((step, i) => (
                    <li key={i} style={{ marginBottom: '8px' }}>{step}</li>
                  ))}
                </ol>
              </div>

              <div className="card" style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)' }}>
                <h4 style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', color: 'var(--accent-green)', marginBottom: '4px' }}>
                  💡 Pro Tip:
                </h4>
                <p style={{ fontSize: '14px' }}>{selected.tips}</p>
              </div>
            </div>
          ) : (
            <div className="card" style={{ height: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📖</div>
              <h3>Selecciona una técnica</h3>
              <p>Haz clic en un método de la izquierda para ver el tutorial paso a paso.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
