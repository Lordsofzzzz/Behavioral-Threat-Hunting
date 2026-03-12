/* ══════════════════════════════════════════════
   SENTINEL CANVAS — EXPORT (PNG / PDF)
   Uses html2canvas + jsPDF from CDN
   ══════════════════════════════════════════════ */

const Exporter = (() => {
  function _showProgress(msg) {
    const m = document.getElementById('export-modal');
    document.getElementById('export-modal-msg').textContent = msg;
    if (m) m.style.display = 'flex';
  }
  function _hideProgress() {
    const m = document.getElementById('export-modal');
    if (m) m.style.display = 'none';
  }

  async function exportPNG() {
    if (typeof html2canvas === 'undefined') {
      Toast.show('html2canvas not loaded', 'error'); return;
    }
    _showProgress('Capturing canvas…');
    try {
      const el = Canvas.getCanvasEl();
      const canvas = await html2canvas(el, {
        backgroundColor: getComputedStyle(document.documentElement)
          .getPropertyValue('--bg').trim() || '#080b10',
        scale: 1.5,
        useCORS: true,
        allowTaint: false,
        logging: false,
      });
      _showProgress('Saving PNG…');
      const link = document.createElement('a');
      link.download = `sentinel-canvas-${_timestamp()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      Toast.show('PNG exported', 'success');
    } catch (err) {
      Toast.show(`Export failed: ${err.message}`, 'error');
    } finally { _hideProgress(); }
  }

  async function exportPDF() {
    if (typeof html2canvas === 'undefined' || typeof jspdf === 'undefined') {
      Toast.show('Export libraries not loaded', 'error'); return;
    }
    _showProgress('Capturing canvas…');
    try {
      const el = Canvas.getCanvasEl();
      const canvas = await html2canvas(el, {
        backgroundColor: getComputedStyle(document.documentElement)
          .getPropertyValue('--bg').trim() || '#080b10',
        scale: 1.5,
        useCORS: true,
        allowTaint: false,
        logging: false,
      });
      _showProgress('Generating PDF…');
      const { jsPDF } = jspdf;
      const imgW = canvas.width;
      const imgH = canvas.height;
      const ratio = imgH / imgW;
      const pdfW = 297; // A4 landscape mm
      const pdfH = pdfW * ratio;
      const pdf = new jsPDF({ orientation: pdfW > pdfH ? 'landscape' : 'portrait', unit: 'mm', format: [pdfW, Math.max(pdfH, 50)] });
      pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', 0, 0, pdfW, pdfH);
      pdf.save(`sentinel-canvas-${_timestamp()}.pdf`);
      Toast.show('PDF exported', 'success');
    } catch (err) {
      Toast.show(`Export failed: ${err.message}`, 'error');
    } finally { _hideProgress(); }
  }

  function _timestamp() {
    return new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
  }

  return { exportPNG, exportPDF };
})();