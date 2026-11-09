import React, { useState } from 'react';

export default function WaferMap({ onSelectDie }) {
  const [hoveredDie, setHoveredDie] = useState(null);

  // Generate a circular 300mm wafer die grid (radius = 7 units)
  const dies = [];
  const radius = 6.2;
  const gridSize = 13;

  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      const x = c - 6;
      const y = r - 6;
      const dist = Math.sqrt(x * x + y * y);

      // Only include dies within circular wafer boundary
      if (dist <= radius) {
        // Deterministic defect simulation based on wafer edge roll-off or hot spot
        const isDefect = (x === 2 && y === 3) || (x === -3 && y === 1) || (x === 4 && y === -4) || (dist > 5.8 && (x * y) % 3 === 0);
        const isWarning = !isDefect && (x === 1 && y === 2) || (dist > 5.5 && Math.abs(x) === 2);
        
        dies.push({
          id: `Die_${r}_${c}`,
          r,
          c,
          x,
          y,
          status: isDefect ? 'DEFECT' : isWarning ? 'WARNING' : 'PASS',
          defectProb: isDefect ? 0.94 : isWarning ? 0.48 : 0.02,
          sensorReading: (100 + (x * 4) + (y * 3) + (isDefect ? 45 : 0)).toFixed(1),
        });
      }
    }
  }

  return (
    <div className="industrial-card p-5 relative overflow-hidden flex flex-col items-center">
      <div className="w-full flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Illustrative 300mm wafer map</h3>
          <p className="text-xs text-slate-400 font-mono">Sample die pattern · select a die for details</p>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500/80"></span>
            <span className="text-slate-400">Pass</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/90 shadow-[0_0_6px_#f43f5e]"></span>
            <span className="text-slate-400">Defect</span>
          </div>
        </div>
      </div>

      {/* Wafer Disc SVG */}
      <div className="relative w-72 h-72 sm:w-80 sm:h-80 flex items-center justify-center my-2">
        {/* Outer silicon wafer rim with alignment notch at bottom */}
        <div className="absolute inset-0 rounded-full border-2 border-slate-700 bg-gradient-to-br from-[#0f172a] via-[#090d16] to-[#040711] shadow-[0_0_30px_rgba(2,132,199,0.1)] flex items-center justify-center">
          {/* Alignment Notch indicator */}
          <div className="absolute bottom-0 w-4 h-1.5 bg-slate-900 border-t border-slate-600 rounded-t-sm" />
        </div>

        {/* Die Grid Container */}
        <div
          className="relative z-10 grid gap-1"
          style={{
            gridTemplateColumns: `repeat(${gridSize}, minmax(0, 1fr))`,
            width: '88%',
            height: '88%',
          }}
        >
          {Array.from({ length: gridSize * gridSize }).map((_, idx) => {
            const r = Math.floor(idx / gridSize);
            const c = idx % gridSize;
            const die = dies.find((d) => d.r === r && d.c === c);

            if (!die) {
              return <div key={idx} className="w-full h-full opacity-0" />;
            }

            const isHovered = hoveredDie?.id === die.id;
            const bgColor =
              die.status === 'DEFECT'
                ? 'bg-rose-500 hover:bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.6)]'
                : die.status === 'WARNING'
                ? 'bg-amber-500/80 hover:bg-amber-400'
                : 'bg-emerald-600/70 hover:bg-emerald-400/90';

            return (
              <button
                key={die.id}
                onMouseEnter={() => setHoveredDie(die)}
                onMouseLeave={() => setHoveredDie(null)}
                onFocus={() => setHoveredDie(die)}
                onBlur={() => setHoveredDie(null)}
                onClick={() => onSelectDie && onSelectDie(die)}
                aria-label={`Die ${die.x}, ${die.y}: ${die.status}, example defect probability ${(die.defectProb * 100).toFixed(1)} percent`}
                className={`w-full h-full rounded-[2px] transition-all duration-150 transform hover:scale-125 hover:z-20 ${bgColor} ${
                  isHovered ? 'ring-2 ring-white' : ''
                }`}
                title={`Die [${die.x}, ${die.y}]: ${die.status}`}
              />
            );
          })}
        </div>
      </div>

      {/* Hover Tooltip Readout */}
      <div className="w-full mt-2 pt-3 border-t border-slate-800 flex items-center justify-between font-mono text-xs text-slate-400 min-h-[32px]">
        {hoveredDie ? (
          <>
            <span className="text-slate-300">
              Die Coord: <strong className="text-sky-400">[{hoveredDie.x}, {hoveredDie.y}]</strong>
            </span>
            <span className="flex items-center space-x-1.5">
              <span>Status:</span>
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  hoveredDie.status === 'DEFECT'
                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                    : hoveredDie.status === 'WARNING'
                    ? 'bg-amber-950 text-amber-300 border border-amber-800'
                    : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                }`}
              >
                {hoveredDie.status}
              </span>
            </span>
            <span>
              Defect Prob: <strong className="text-slate-200">{(hoveredDie.defectProb * 100).toFixed(1)}%</strong>
            </span>
          </>
        ) : (
          <span className="text-slate-500 italic text-center w-full">Hover over any wafer die to inspect telemetry</span>
        )}
      </div>
    </div>
  );
}
