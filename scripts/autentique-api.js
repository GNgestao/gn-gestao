const express = require('express');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');

const app = express();
app.use(express.json({ limit: '10mb' }));

const AUTENTIQUE_TOKEN = '7a20bb2e1c17def3620d7f426153e2cf3a530497262450bdb8c96b415f583824';
const PORT = 5052;
const TMP_DIR = '/tmp/autentique';

if (!fs.existsSync(TMP_DIR)) fs.mkdirSync(TMP_DIR, { recursive: true });

app.post('/assinar', async (req, res) => {
  const { html, titulo, participantes } = req.body;

  if (!html || !titulo || !participantes || !Array.isArray(participantes)) {
    return res.status(400).json({ erro: 'Campos obrigatórios: html, titulo, participantes (array)' });
  }

  const timestamp = Date.now();
  const htmlFile = path.join(TMP_DIR, `doc_${timestamp}.html`);
  const pdfFile = path.join(TMP_DIR, `doc_${timestamp}.pdf`);

  try {
    // 1. Salvar HTML
    fs.writeFileSync(htmlFile, html, 'utf8');

    // 2. Converter HTML → PDF com wkhtmltopdf
    execSync(`wkhtmltopdf --quiet --page-size A4 --margin-top 10mm --margin-bottom 10mm --margin-left 15mm --margin-right 15mm "${htmlFile}" "${pdfFile}"`);

    // 3. Ler PDF como base64
    const pdfBase64 = fs.readFileSync(pdfFile).toString('base64');

    // 4. Montar signatários para a mutation do Autentique
    const signatarios = participantes.map(p => ({
      email: p.email,
      action: { name: 'SIGN' },
      positions: [{ element: 'endorsement', x: '0.5', y: '0.8', z: '1' }]
    }));

    // 5. Enviar para Autentique via GraphQL
    const mutation = `
      mutation CreateDocument($document: DocumentInput!, $signers: [SignerInput!]!, $file: Upload!) {
        createDocument(document: $document, signers: $signers, file: $file) {
          id
          name
          signatures {
            public_id
            name
            email
            link { short_link }
            action { name }
          }
        }
      }
    `;

    const operations = JSON.stringify({
      query: mutation,
      variables: {
        document: { name: titulo },
        signers: signatarios,
        file: null
      }
    });

    const map = JSON.stringify({ '0': ['variables.file'] });

    const FormData = require('form-data');
    const form = new FormData();
    form.append('operations', operations);
    form.append('map', map);
    form.append('0', fs.createReadStream(pdfFile), {
      filename: `${titulo}.pdf`,
      contentType: 'application/pdf'
    });

    const response = await fetch('https://api.autentique.com.br/v2/graphql', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTENTIQUE_TOKEN}`,
        ...form.getHeaders()
      },
      body: form
    });

    const data = await response.json();

    if (data.errors) {
      throw new Error(JSON.stringify(data.errors));
    }

    const doc = data.data.createDocument;

    // 6. Encontrar link do Gabriel (email TKE)
    const gabrielSig = doc.signatures.find(s =>
      s.email && s.email.includes('tkelevator')
    );
    const gabrielLink = gabrielSig?.link?.short_link || null;

    // 7. Limpar arquivos temporários
    fs.unlinkSync(htmlFile);
    fs.unlinkSync(pdfFile);

    return res.json([{
      sucesso: true,
      documentoId: doc.id,
      gabrielLink: gabrielLink,
      assinaturas: doc.signatures.map(s => ({
        nome: s.name,
        email: s.email,
        link: s.link?.short_link
      }))
    }]);

  } catch (err) {
    // Limpar arquivos em caso de erro
    try { if (fs.existsSync(htmlFile)) fs.unlinkSync(htmlFile); } catch {}
    try { if (fs.existsSync(pdfFile)) fs.unlinkSync(pdfFile); } catch {}
    console.error('Erro Autentique:', err.message);
    return res.status(500).json({ sucesso: false, erro: err.message });
  }
});

app.get('/health', (req, res) => res.json({ status: 'ok', porta: PORT }));

app.listen(PORT, () => console.log(`Autentique API rodando na porta ${PORT}`));
