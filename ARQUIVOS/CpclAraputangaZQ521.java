package br.com.fiorilli.leitura.print.cpcl.ZQ521;

import android.content.Context;
import br.com.fiorilli.fiorilliandroidutils.Utils;
import br.com.fiorilli.fiorilliandroidutils.boletos.BoletoUtils;
import br.com.fiorilli.leitura.print.cpcl.Cpcl;
import br.com.fiorilli.leitura.vo.agua.AgFatsimultaneohistoricoVO;
import br.com.fiorilli.leitura.vo.agua.AgFatsimultaneolancaVO;
import br.com.fiorilli.leitura.vo.agua.AgFaturamentosimultaneoVO;
import br.com.fiorilli.leitura.vo.agua.AgLeiturasAndroidVO;
import br.com.fiorilli.leitura.vo.agua.AgQualidadeVO;
import br.com.fiorilli.leitura.vo.agua.AgRocorrVO;
import br.com.fiorilli.leitura.vo.app.ConfVO;
import br.com.fiorilli.leitura.vo.geral.GrCadEmpresaVO;
import com.bxl.BXLConst;
import com.ibm.icu.impl.locale.LanguageTag;
import com.ibm.icu.lang.UCharacter;
import com.ibm.icu.text.DateFormat;
import com.j256.ormlite.support.ConnectionSource;
import java.math.BigDecimal;
import java.sql.SQLException;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import mf.org.apache.xerces.impl.xs.SchemaSymbols;
import org.apache.commons.lang3.StringUtils;
import org.joda.time.DateTime;
/* loaded from: classes11.dex */
public class CpclAraputangaZQ521 extends Cpcl {
    private DecimalFormat df;

    public CpclAraputangaZQ521(Context context, GrCadEmpresaVO empresa, AgLeiturasAndroidVO leiturasVO, ConnectionSource connectionSource, BigDecimal valorPagar, ConfVO configuracoes) {
        super(context, empresa, leiturasVO, connectionSource, valorPagar, configuracoes);
        this.df = new DecimalFormat("##0.00");
        initDecimalFormat();
    }

    @Override // br.com.fiorilli.leitura.print.cpcl.Cpcl
    public String getHeaderLabel() {
        return "! 0 200 200 230 1\r\nIN-MILLIMETERS\r\nCOUNTRY LATIN9\r\n";
    }

    public void initDecimalFormat() {
        this.df = new DecimalFormat("##0.00");
        DecimalFormatSymbols sym = DecimalFormatSymbols.getInstance();
        sym.setDecimalSeparator(',');
        this.df.setDecimalFormatSymbols(sym);
    }

    @Override // br.com.fiorilli.leitura.print.cpcl.Cpcl
    public String getBodyLabel(AgFaturamentosimultaneoVO fatsimultaneoVO, List<AgFatsimultaneohistoricoVO> agFatsimultaneohistoricoVOs, List<AgFatsimultaneolancaVO> agFatsimultaneolancaVOs, String referencia, AgRocorrVO ocorrencia, boolean isDebitoAutomatico) throws ParseException, SQLException {
        return getHeaderLabel().concat(montarCpcl(fatsimultaneoVO, agFatsimultaneohistoricoVOs, agFatsimultaneolancaVOs, referencia, ocorrencia, isDebitoAutomatico));
    }

    private String montarCpcl(AgFaturamentosimultaneoVO fatsimultaneoVO, List<AgFatsimultaneohistoricoVO> agFatsimultaneohistoricoVOs, List<AgFatsimultaneolancaVO> agFatsimultaneolancaVOs, String referencia, AgRocorrVO ocorrencia, boolean isDebitoAutomatico) throws ParseException {
        int y;
        StringBuilder sequencia;
        StringBuilder sbEnderecoEntrega;
        StringBuilder sb = new StringBuilder();
        String linhaSuperior = getLinhaHorizontal(2, 15, 100);
        String linhaEsquerda = getLinhaVertical(2, 15, UCharacter.UnicodeBlock.MEETEI_MAYEK_ID);
        String linhaDireita = getLinhaVertical(100, 15, UCharacter.UnicodeBlock.MEETEI_MAYEK_ID);
        String linhaInferior = getLinhaHorizontal(2, UCharacter.UnicodeBlock.MEETEI_MAYEK_ID, 100);
        String linhaVertical1 = getLinhaVertical(76, 15, 39);
        String linhaHorizontal1 = getLinhaHorizontal(76, 22, 100);
        String linhaHorizontal2 = getLinhaHorizontal(76, 30, 100);
        String linhaHorizontal3 = getLinhaHorizontal(76, 34, 100);
        String linhaHorizontal4 = getLinhaHorizontal(2, 39, 100);
        String linhaHorizontal5 = getLinhaHorizontal(2, 44, 100);
        sb.append(linhaSuperior).append("\r\n");
        sb.append(linhaEsquerda).append("\r\n");
        sb.append(linhaDireita).append("\r\n");
        sb.append(linhaInferior).append("\r\n");
        sb.append(linhaVertical1).append("\r\n");
        sb.append(linhaHorizontal1).append("\r\n");
        sb.append(linhaHorizontal2).append("\r\n");
        sb.append(linhaHorizontal3).append("\r\n");
        sb.append(linhaHorizontal4).append("\r\n");
        sb.append(linhaHorizontal5).append("\r\n");
        String nomeCompromissario = !Utils.isNullOrEmpty(this.leiturasVO.getNomeeCnt()) ? Utils.removeAcentos(this.leiturasVO.getNomeeCnt()) : "";
        StringBuilder sbEnderecoInstalacao = new StringBuilder();
        boolean isNullOrEmpty = Utils.isNullOrEmpty(this.leiturasVO.getNomeLog());
        String str = StringUtils.SPACE;
        String linhaSuperior2 = !isNullOrEmpty ? Utils.removeAcentos(this.leiturasVO.getNomeLog()) + ", " : StringUtils.SPACE;
        sbEnderecoInstalacao.append(linhaSuperior2).append(!Utils.isNull(this.leiturasVO.getNumeroCag()) ? this.leiturasVO.getNumeroCag().toString() : StringUtils.SPACE).append(", ").append(!Utils.isNullOrEmpty(this.leiturasVO.getNomeBai()) ? Utils.removeAcentos(this.leiturasVO.getNomeBai()) : StringUtils.SPACE);
        String cep = !Utils.isNullOrEmpty(this.leiturasVO.getCepCag()) ? this.leiturasVO.getCepCag() : StringUtils.SPACE;
        String rota = !Utils.isNullOrEmpty(this.leiturasVO.getCodRotaCag()) ? this.leiturasVO.getCodRotaCag() : "";
        StringBuilder sbEnderecoEntrega2 = new StringBuilder();
        sbEnderecoEntrega2.append(!Utils.isNullOrEmpty(this.leiturasVO.getLograeCag()) ? Utils.removeAcentos(this.leiturasVO.getLograeCag()) + ", " : StringUtils.SPACE).append(!Utils.isNull(this.leiturasVO.getNumeroeCag()) ? this.leiturasVO.getNumeroeCag().toString() : StringUtils.SPACE).append(", ").append(!Utils.isNullOrEmpty(this.leiturasVO.getBairroeCag()) ? Utils.removeAcentos(this.leiturasVO.getBairroeCag()) : StringUtils.SPACE).append("\r\n");
        StringBuilder sequencia2 = new StringBuilder();
        sequencia2.append(!Utils.isNullOrEmpty(this.leiturasVO.getSetorCag()) ? this.leiturasVO.getSetorCag() : StringUtils.SPACE).append(" - ");
        sequencia2.append(!Utils.isNull(this.leiturasVO.getSeqeCag()) ? this.leiturasVO.getSeqeCag() : StringUtils.SPACE).append(" - ");
        sequencia2.append(!Utils.isNullOrEmpty(this.leiturasVO.getCodRotaeCag()) ? this.leiturasVO.getCodRotaeCag() : "  ");
        String instalacao = this.leiturasVO.getInstalacaoCag();
        sb.append("T 7 0 3 16 ").append(nomeCompromissario).append("\r\n");
        String linhaHorizontal32 = sbEnderecoInstalacao.toString();
        Map<String, Object> mapEnderecoLeituras = formatarMensagem(3, 19, linhaHorizontal32, 65);
        String enderecoFormatado = (String) mapEnderecoLeituras.get("mensagem");
        int y2 = ((Integer) mapEnderecoLeituras.get(DateFormat.YEAR)).intValue();
        String nomeCompromissario2 = nomeCompromissario;
        sb.append(enderecoFormatado).append("\r\n");
        sb.append("T 7 0 3 ").append(y2).append(" CEP: ").append(cep).append(", Rota: ").append(rota).append("\r\n");
        int y3 = y2 + 3;
        sb.append("T 7 0 3 ").append(y3).append(" END. ENT: ").append((CharSequence) sbEnderecoEntrega2).append("\r\n");
        int y4 = y3 + 3;
        sb.append("T 7 0 3 ").append(y4).append(" Sequencia anterior: ").append((CharSequence) sequencia2).append("\r\n");
        sb.append("T 7 0 3 ").append(y4 + 3).append(" LIGACAO: ").append(instalacao).append("\r\n");
        sb.append("T 7 2 78 15 MES/ANO: ").append(referencia).append("\r\n");
        sb.append("T 7 0 78 23 NR. GUIA ").append("\r\n").append("\r\n");
        sb.append("T 7 0 78 26 ").append(fatsimultaneoVO.getNnumeroFsi()).append("\r\n");
        sb.append("T 7 0 78 31 CATEGORIA/QTDE ").append("\r\n");
        sb.append("T 7 0 82 35 ").append(this.leiturasVO.getDescrPrl()).append("\r\n");
        sb.append("T 7 0 30 40 DESCRICAO ").append("\r\n");
        sb.append("T 7 0 89 40 VALOR ").append("\r\n");
        int y5 = 45;
        Iterator<AgFatsimultaneolancaVO> it = agFatsimultaneolancaVOs.iterator();
        while (true) {
            Iterator<AgFatsimultaneolancaVO> it2 = it;
            if (!it.hasNext()) {
                break;
            }
            String instalacao2 = instalacao;
            AgFatsimultaneolancaVO lancamento = it2.next();
            if (lancamentoDeResiduo(lancamento)) {
                Map<String, String> map = formatarLancamento(lancamento);
                sequencia = sequencia2;
                String descricao = map.get("descricao");
                sbEnderecoEntrega = sbEnderecoEntrega2;
                String valor = map.get("valor");
                sb.append("T 7 0 5 ").append(y5).append("  ").append(descricao).append("\r\n");
                sb.append("T 7 0 87 ").append(y5).append("  ").append(valor).append("\r\n");
                y5 += 3;
            } else {
                sequencia = sequencia2;
                sbEnderecoEntrega = sbEnderecoEntrega2;
                if (validarImpressaoLancamentoAcimaDeZero(lancamento)) {
                    sb.append("T 7 0 5 ").append(y5).append(StringUtils.SPACE).append(Utils.removeAcentos(lancamento.getDescricaoFsl())).append("\r\n");
                    sb.append("T 7 0 87 ").append(y5).append("  ").append(this.df.format(lancamento.getValorFsl())).append("\r\n");
                    y5 += 3;
                }
            }
            it = it2;
            sequencia2 = sequencia;
            instalacao = instalacao2;
            sbEnderecoEntrega2 = sbEnderecoEntrega;
        }
        StringBuilder sequencia3 = sequencia2;
        String instalacao3 = instalacao;
        StringBuilder sbEnderecoEntrega3 = sbEnderecoEntrega2;
        if (fatsimultaneoVO.getCreditofuturoFsi().doubleValue() != 0.0d) {
            sb.append("T 7 0 5 ").append(y5).append(StringUtils.SPACE).append("Restituicao ").append("\r\n");
            sb.append("T 7 0 87 ").append(y5).append(StringUtils.SPACE).append(formatarValorCredito(fatsimultaneoVO.getCreditofuturoFsi())).append("\r\n");
        }
        String linhaHorizontal6 = getLinhaHorizontal(2, 80, 100);
        String linhaVertical2 = getLinhaVertical(28, 80, 89);
        String linhaVertical3 = getLinhaVertical(50, 80, 89);
        String linhaVertical4 = getLinhaVertical(78, 80, 89);
        int y6 = y5;
        String rota2 = rota;
        String linhaHorizontal7 = getLinhaHorizontal(2, 89, 100);
        sb.append("T 0 2 4 80 DATA LEITURA ANTERIOR ").append("\r\n");
        sb.append("T 7 2 5 83 ").append(!Utils.isNullOrEmpty(this.leiturasVO.getDataLeituraAnterior()) ? Utils.format(this.leiturasVO.getDataLeituraAnterior()) : StringUtils.SPACE).append("\r\n");
        sb.append("T 0 2 30 80 DATA LEITURA ATUAL ").append("\r\n");
        sb.append("T 7 2 30 83 ").append(Utils.format(this.leiturasVO.getDthLeitAlt())).append("\r\n");
        sb.append("T 0 2 60 80 VENCIMENTO ").append("\r\n");
        sb.append("T 7 2 56 83 ").append(Utils.format(fatsimultaneoVO.getDatavenciFsi())).append("\r\n");
        sb.append("T 0 2 80 80 VALOR A PAGAR").append("\r\n");
        sb.append("T 7 2 82 83 R$ ").append(this.df.format(getValorPagar())).append("\r\n");
        sb.append(linhaHorizontal6).append("\r\n");
        sb.append(linhaVertical2).append("\r\n");
        sb.append(linhaVertical3).append("\r\n");
        sb.append(linhaVertical4).append("\r\n");
        sb.append(linhaHorizontal7).append("\r\n");
        String linhaVertical5 = getLinhaVertical(25, 89, 97);
        String linhaVertical6 = getLinhaVertical(44, 89, 97);
        String linhaVertical7 = getLinhaVertical(60, 89, 97);
        String linhaVertical8 = getLinhaVertical(78, 89, 97);
        String linhaHorizontal8 = getLinhaHorizontal(2, 97, 100);
        String cep2 = cep;
        String linhaHorizontal9 = getLinhaHorizontal(2, 105, 100);
        sb.append(linhaVertical5).append("\r\n");
        sb.append(linhaVertical6).append("\r\n");
        sb.append(linhaVertical7).append("\r\n");
        sb.append(linhaVertical8).append("\r\n");
        sb.append(linhaHorizontal8).append("\r\n");
        sb.append(linhaHorizontal9).append("\r\n");
        sb.append("T 0 2 7 89 LEITURA ANTERIOR ").append("\r\n");
        sb.append("T 0 2 28 89 LEITURA ATUAL ").append("\r\n");
        sb.append("T 0 2 45 89 CONSUMO REAL ").append("\r\n");
        sb.append("T 0 2 61 89 CONS. FATURADO ").append("\r\n");
        sb.append("T 0 2 86 89 MEDIA ").append("\r\n");
        sb.append("T 5 0 9 93 ").append(!Utils.isNull(this.leiturasVO.getValLantAlt()) ? Integer.valueOf(this.leiturasVO.getValLantAlt().intValue()) : StringUtils.SPACE).append("\r\n");
        sb.append("T 5 0 30 93 ").append(this.leiturasVO.getValLeitAlt().intValue()).append("\r\n");
        sb.append("T 5 0 50 93 ").append(this.leiturasVO.getValConsatuAlt()).append("\r\n");
        sb.append("T 5 0 66 93 ").append(this.leiturasVO.getValConsfatAlt()).append("\r\n");
        sb.append("T 5 0 87 93 ").append(!Utils.isNull(this.leiturasVO.getValConsmedAlt()) ? Integer.valueOf(this.leiturasVO.getValConsmedAlt().intValue()) : StringUtils.SPACE).append("\r\n");
        String linhaVertical9 = getLinhaVertical(44, 97, 105);
        String linhaVertical10 = getLinhaVertical(60, 97, 105);
        String linhaVertical11 = getLinhaVertical(78, 97, 105);
        sb.append(linhaVertical9).append("\r\n");
        sb.append(linhaVertical10).append("\r\n");
        sb.append(linhaVertical11).append("\r\n");
        sb.append("T 0 2 15 97 NR. DO HIDROMETRO ").append("\r\n");
        sb.append("T 0 2 50 97 VAZAO ").append("\r\n");
        sb.append("T 0 2 64 97 DIAMETRO ").append("\r\n");
        sb.append("T 0 2 80 97 DATA DE INSTALACAO ").append("\r\n");
        sb.append("T 5 0 15 101 ").append(!Utils.isNull(this.leiturasVO.getNroHdr()) ? this.leiturasVO.getNroHdr() : StringUtils.SPACE).append("\r\n");
        sb.append("T 5 0 50 101 ").append(!Utils.isNull(this.leiturasVO.getVazaonThr()) ? this.leiturasVO.getVazaonThr() : StringUtils.SPACE).append("\r\n");
        sb.append("T 5 0 66 101 ").append(!Utils.isNull(this.leiturasVO.getDiametroThr()) ? this.leiturasVO.getDiametroThr() : StringUtils.SPACE).append("\r\n");
        if (!Utils.isNullOrEmpty(this.leiturasVO.getDtaCadCag())) {
            sb.append("T 5 0 82 101 ").append(Utils.format(this.leiturasVO.getDtaCadCag())).append("\r\n");
        }
        String linhaHorizontal10 = getLinhaHorizontal(2, 110, 100);
        sb.append(linhaHorizontal10).append("\r\n");
        sb.append("T 7 0 4 107 OCORRENCIA: ").append(ocorrencia.getDescrAoc()).append("\r\n");
        sb.append(getLinhaVertical(44, 110, 144)).append("\r\n");
        sb.append("T 0 2 4 110 DADOS DOS ULTIMOS 6 MESES ").append("\r\n");
        sb.append(getLinhaHorizontal(2, 114, 44)).append("\r\n");
        sb.append("T 0 2 4 114 MES ").append("\r\n");
        sb.append("T 0 2 18 114 CONSUMO ").append("\r\n");
        sb.append("T 0 2 31 114 DIAS ").append("\r\n");
        sb.append("T 0 2 38 114 MEDIA ").append("\r\n");
        if (agFatsimultaneohistoricoVOs.isEmpty()) {
            y = y6;
        } else {
            y = 118;
            Iterator<AgFatsimultaneohistoricoVO> it3 = agFatsimultaneohistoricoVOs.iterator();
            while (it3.hasNext()) {
                AgFatsimultaneohistoricoVO historico = it3.next();
                Iterator<AgFatsimultaneohistoricoVO> it4 = it3;
                String linhaHorizontal92 = linhaHorizontal9;
                sb.append("T 7 0 4 ").append(y).append(StringUtils.SPACE).append(historico.getReferhistFsh()).append("\r\n");
                sb.append("T 7 0 20 ").append(y).append(StringUtils.SPACE).append(historico.getConsumoFsh()).append("\r\n");
                sb.append("T 7 0 31 ").append(y).append(StringUtils.SPACE).append(historico.getNdiasFsh()).append("\r\n");
                sb.append("T 7 0 38 ").append(y).append("  ").append(!Utils.isNull(historico.getMediaFsh()) ? Integer.valueOf(historico.getMediaFsh().intValue()) : SchemaSymbols.ATTVAL_FALSE_0).append("\r\n");
                y += 3;
                it3 = it4;
                linhaHorizontal9 = linhaHorizontal92;
            }
        }
        sb.append("T 0 2 45 110 MENSAGEM").append("\r\n");
        if (this.isExibirMensagemFatura) {
            y = 115;
            if (!Utils.isNullOrEmpty(fatsimultaneoVO.getMensagemdebitoFsi())) {
                Map mapMensagem = formatarMensagem(45, 115, fatsimultaneoVO.getMensagemdebitoFsi(), 32);
                sb.append(mapMensagem.get("mensagem")).append("\r\n");
                y = ((Integer) mapMensagem.get(DateFormat.YEAR)).intValue();
            }
            if (y < 154) {
                if (!Utils.isNullOrEmpty(fatsimultaneoVO.getMensagemfaturaFsi())) {
                    Map mapMensagem2 = formatarMensagem(45, y, fatsimultaneoVO.getMensagemfaturaFsi(), 32);
                    sb.append(mapMensagem2.get("mensagem")).append("\r\n");
                    y = ((Integer) mapMensagem2.get(DateFormat.YEAR)).intValue();
                }
                if (!Utils.isNullOrEmpty(fatsimultaneoVO.getMensagemcontasabertoFsi())) {
                    sb.append(formatarMensagem(45, y, fatsimultaneoVO.getMensagemfaturaFsi(), 32).get("mensagem")).append("\r\n");
                }
            }
        }
        sb.append(getLinhaHorizontal(2, 144, 100)).append("\r\n");
        sb.append("T 0 2 10 144 DETALHES SOBRE ").append("\r\n");
        sb.append("T 0 2 8 147 LEGISLACAO VIDE VERSO").append("\r\n");
        sb.append(getLinhaVertical(35, 144, 151)).append("\r\n");
        AgQualidadeVO qualidadeVO = getAgQualidadeVO();
        if (!Utils.isNull(qualidadeVO)) {
            StringBuilder append = sb.append("T 0 2 42 145 PERIODO DA ANALISE: ");
            if (!Utils.isNull(qualidadeVO.getDataAql())) {
                str = Utils.format(qualidadeVO.getDataAql());
            }
            append.append(str).append("\r\n");
        }
        sb.append(getLinhaHorizontal(2, 151, 100)).append("\r\n");
        sb.append("T 0 2 10 152 PARAMETRO ").append("\r\n");
        sb.append("T 0 2 28 152 UNIDADE ").append("\r\n");
        sb.append("T 0 2 47 152 VMP ").append("\r\n");
        sb.append("T 0 2 60 151 TOTAL DE ANALISES ").append("\r\n");
        sb.append("T 0 2 64 154 REALIZADAS ").append("\r\n");
        sb.append("T 0 2 87 151 VALOR MEDIO ").append("\r\n");
        sb.append("T 0 2 87 154 DETECTADO ").append("\r\n");
        sb.append(getAnaliseAgua()).append("\r\n");
        sb.append(getLinhaHorizontal(2, 157, 100)).append("\r\n");
        DateTime dateTimeEmissao = new DateTime();
        SimpleDateFormat sdf = new SimpleDateFormat("dd/MM/yyyy");
        String dataEmissao = sdf.format(dateTimeEmissao.toDate());
        SimpleDateFormat sdf2 = new SimpleDateFormat("HH:mm");
        String horaEmissao = sdf2.format(dateTimeEmissao.toDate());
        sb.append("T 0 2 3 180 FAVOR AUTENTICAR NO VERSO - DEVOLVER AO USUARIO").append("\r\n");
        sb.append("T 0 2 76 180 EMISSAO: ").append(dataEmissao).append(BXLConst.PORT_DELIMITER).append(horaEmissao).append("\r\n");
        sb.append(getLinhaHorizontal(2, UCharacter.UnicodeBlock.MEETEI_MAYEK_ID, 100)).append("\r\n");
        sb.append(getLinhaVertical(2, UCharacter.UnicodeBlock.MEETEI_MAYEK_ID, 206)).append("\r\n");
        sb.append(getLinhaVertical(100, UCharacter.UnicodeBlock.MEETEI_MAYEK_ID, 206)).append("\r\n");
        sb.append(getLinhaHorizontal(2, 199, 100)).append("\r\n");
        sb.append("T 7 0 3 184 ").append(nomeCompromissario2).append("\r\n");
        sb.append("T 7 0 3 187 ").append((CharSequence) sbEnderecoInstalacao).append("\r\n");
        sb.append("T 7 0 3 190 ").append(cep2).append(", Rota: ").append(rota2).append("\r\n");
        sb.append("T 7 0 3 193 END. ENT: ").append((CharSequence) sbEnderecoEntrega3).append("\r\n");
        sb.append("T 7 0 3 196 Sequencia anterior: ").append((CharSequence) sequencia3).append("\r\n");
        sb.append("T 7 0 78 184 MES/ANO: ").append(referencia).append("\r\n");
        sb.append(getLinhaHorizontal(76, UCharacter.UnicodeBlock.OLD_SOUTH_ARABIAN_ID, 100)).append("\r\n");
        sb.append("T 7 0 78 187.5 NR. GUIA ").append("\r\n").append("\r\n");
        sb.append("T 7 0 78 190 ").append(fatsimultaneoVO.getNnumeroFsi()).append("\r\n");
        sb.append(getLinhaHorizontal(76, UCharacter.UnicodeBlock.KAITHI_ID, 100)).append("\r\n");
        sb.append("T 7 0 78 193 CATEGORIA/QTDE ").append("\r\n");
        sb.append("T 7 0 82 196 ").append(this.leiturasVO.getDescrPrl()).append("\r\n");
        sb.append("T 7 0 12 200 LIGACAO ").append("\r\n");
        sb.append("T 7 0 12 203 ").append(instalacao3).append("\r\n");
        sb.append(getLinhaVertical(35, 199, 206)).append("\r\n");
        sb.append("T 7 0 47 200 VENCIMENTO ").append("\r\n");
        sb.append("T 7 0 47 203 ").append(Utils.format(fatsimultaneoVO.getDatavenciFsi())).append("\r\n");
        sb.append("T 7 0 80 200 VALOR A PAGAR ").append("\r\n");
        sb.append("T 7 0 82 203 R$ ").append(this.df.format(getValorPagar())).append("\r\n");
        sb.append(getLinhaVertical(76, UCharacter.UnicodeBlock.MEETEI_MAYEK_ID, 206)).append("\r\n");
        sb.append(getLinhaHorizontal(2, 206, 100)).append("\r\n");
        sb.append("CENTER\r\n");
        if (!isDebitoAutomatico) {
            if (getValorPagar().compareTo(BigDecimal.ZERO) > 0.0d) {
                sb.append("T 5 0 0 208 ").append(BoletoUtils.isGuiaArrecadacao(fatsimultaneoVO.getCodbarraFsi()).booleanValue() ? BoletoUtils.getLinhaDigitavelArrecadacao(fatsimultaneoVO.getCodbarraFsi()) : BoletoUtils.getLinhaDigitavel(fatsimultaneoVO.getCodbarraFsi())).append("\r\n");
                sb.append("B I2OF5 0.245 25 8 0 212 ").append(fatsimultaneoVO.getCodbarraFsi()).append("\r\n");
            }
        } else {
            sb.append("CENTER\r\n");
            sb.append("T 5 0 0 209 DEBITO AUTOMATICO NAO RECEBER").append("\r\n");
            sb.append("LEFT\r\n");
            sb.append("T 7 0 5 213 Banco: ").append(this.leiturasVO.getBancoCag()).append("\r\n");
            sb.append("T 7 0 30 213 Agencia: ").append(this.leiturasVO.getAgenciaCag()).append("\r\n");
            sb.append("T 7 0 60 213 Conta: ").append(this.leiturasVO.getContaCag()).append("\r\n");
        }
        sb.append("FORM\r\n");
        sb.append("PRINT\r\n");
        return sb.toString();
    }

    @Override // br.com.fiorilli.leitura.print.cpcl.Cpcl
    public String getTaxaLixo(AgLeiturasAndroidVO leiturasVO, AgFaturamentosimultaneoVO fatsimultaneoVO, String referencia) throws ParseException {
        String str;
        String complemento;
        DecimalFormat df = new DecimalFormat("##0.00");
        DecimalFormatSymbols sym = DecimalFormatSymbols.getInstance();
        sym.setDecimalSeparator(',');
        df.setDecimalFormatSymbols(sym);
        StringBuilder sb = new StringBuilder("! 0 200 200 230 1\r\n");
        sb.append("IN-MILLIMETERS\r\n");
        sb.append("COUNTRY LATIN9\r\n");
        String linhaSuperior = getLinhaHorizontal(2, 20, 100);
        String linhaEsquerda = getLinhaVertical(2, 20, 174);
        String linhaDireita = getLinhaVertical(100, 20, 174);
        String linhaInferior = getLinhaHorizontal(2, 174, 100);
        sb.append(linhaSuperior).append("\r\n");
        sb.append(linhaEsquerda).append("\r\n");
        sb.append(linhaDireita).append("\r\n");
        sb.append(linhaInferior).append("\r\n");
        String linhaHorizontal = getLinhaHorizontal(2, 44, 100);
        String linhaVertical = getLinhaVertical(50, 44, 52);
        String linhaHorizontalFinal = getLinhaHorizontal(2, 52, 100);
        sb.append(linhaHorizontal).append("\r\n");
        sb.append(linhaVertical).append("\r\n");
        sb.append(linhaHorizontalFinal).append("\r\n");
        String ladoSuperior1 = getLinhaHorizontal(2, UCharacter.UnicodeBlock.EGYPTIAN_HIEROGLYPHS_ID, 50);
        String ladoEsquerdo1 = getLinhaVertical(2, UCharacter.UnicodeBlock.EGYPTIAN_HIEROGLYPHS_ID, 200);
        String ladoDireito1 = getLinhaVertical(50, UCharacter.UnicodeBlock.EGYPTIAN_HIEROGLYPHS_ID, 200);
        String ladoInferior1 = getLinhaHorizontal(2, 200, 50);
        sb.append(ladoSuperior1).append("\r\n");
        sb.append(ladoEsquerdo1).append("\r\n");
        sb.append(ladoDireito1).append("\r\n");
        sb.append(ladoInferior1).append("\r\n");
        String ladoSuperior2 = getLinhaHorizontal(2, 201, 50);
        String ladoEsquerdo2 = getLinhaVertical(2, 201, 207);
        String ladoDireito2 = getLinhaVertical(50, 201, 207);
        String ladoInferior2 = getLinhaHorizontal(2, 207, 50);
        sb.append(ladoSuperior2).append("\r\n");
        sb.append(ladoEsquerdo2).append("\r\n");
        sb.append(ladoDireito2).append("\r\n");
        sb.append(ladoInferior2).append("\r\n");
        String ladoSuperior3 = getLinhaHorizontal(51, 201, 100);
        String ladoEsquerdo3 = getLinhaVertical(51, 201, 207);
        String ladoDireito3 = getLinhaVertical(100, 201, 207);
        String ladoInferior3 = getLinhaHorizontal(51, 207, 100);
        sb.append(ladoSuperior3).append("\r\n");
        sb.append(ladoEsquerdo3).append("\r\n");
        sb.append(ladoDireito3).append("\r\n");
        sb.append(ladoInferior3).append("\r\n");
        String nomeCompromissario = !Utils.isNullOrEmpty(leiturasVO.getNomeCnt()) ? Utils.removeAcentos(leiturasVO.getNomeCnt()) : "";
        StringBuilder sbEndereco = new StringBuilder();
        boolean isNullOrEmpty = Utils.isNullOrEmpty(leiturasVO.getLograeCag());
        String str2 = StringUtils.SPACE;
        if (isNullOrEmpty) {
            str = StringUtils.SPACE;
        } else {
            StringBuilder sb2 = new StringBuilder();
            String ladoInferior32 = Utils.removeAcentos(leiturasVO.getLograeCag());
            str = sb2.append(ladoInferior32).append(", ").toString();
        }
        StringBuilder append = sbEndereco.append(str);
        String ladoDireito32 = !Utils.isNull(leiturasVO.getNumeroeCag()) ? leiturasVO.getNumeroeCag().toString() : StringUtils.SPACE;
        append.append(ladoDireito32);
        if (Utils.isNullOrEmpty(leiturasVO.getCepeCag())) {
            complemento = " , " + (!Utils.isNullOrEmpty(leiturasVO.getBairroeCag()) ? Utils.removeAcentos(leiturasVO.getBairroeCag()) : StringUtils.SPACE) + Utils.removeAcentos(leiturasVO.getNomeCid()) + leiturasVO.getUfCid();
        } else {
            complemento = leiturasVO.getCepeCag();
        }
        String rota = !Utils.isNullOrEmpty(leiturasVO.getCodRotaCag()) ? leiturasVO.getCodRotaCag() : "";
        String sequencia = Utils.isNull(leiturasVO.getSeqeCag()) ? "" : leiturasVO.getSeqeCag().toString();
        sb.append("T 7 2 3 22 ").append(nomeCompromissario).append("\r\n");
        sb.append("T 7 0 3 28 ").append((CharSequence) sbEndereco).append("\r\n");
        sb.append("T 7 0 3 31 ").append(complemento).append("\r\n");
        sb.append("T 7 0 3 34 Rota: ").append(rota).append("\r\n");
        sb.append("T 7 0 3 37 ENDERECO ENTREGA").append("\r\n");
        sb.append("T 7 0 3 40 Sequencia anterior: ").append(sequencia).append("\r\n");
        sb.append("T 0 3 15 44 COD.LIGACAO ").append("\r\n");
        StringBuilder append2 = sb.append("T 7 0 18 48 ");
        String ladoEsquerdo32 = leiturasVO.getInstalacaoCag();
        append2.append(ladoEsquerdo32).append("\r\n");
        sb.append("T 0 3 56 44 NUMERO DO HIDROMETRO ").append("\r\n");
        StringBuilder append3 = sb.append("T 7 0 64 48 ");
        if (!Utils.isNullOrEmpty(leiturasVO.getNroHdr())) {
            str2 = leiturasVO.getNroHdr();
        }
        append3.append(str2).append("\r\n");
        sb.append("CENTER\r\n");
        sb.append("T 5 2 0 53 TAXA DE LIXO").append("\r\n");
        sb.append("LEFT\r\n");
        sb.append("T 0 3 3 150 DESCRICAO").append("\r\n");
        sb.append("T 7 0 3 154 TARIFA DE COLETA DE LIXO").append("\r\n");
        sb.append("T 0 3 90 150 VALOR").append("\r\n");
        sb.append("T 7 0 92 154 ").append(df.format(fatsimultaneoVO.getLixoValorFsi())).append("\r\n");
        sb.append("LEFT\r\n");
        DateTime dateTimeEmissao = new DateTime();
        SimpleDateFormat sdf = new SimpleDateFormat("dd/MM/yyyy");
        String dataEmissao = sdf.format(dateTimeEmissao.toDate());
        String horaEmissao = dateTimeEmissao.toString("HH:mm");
        sb.append("T 0 2 15 177 DATA EMISSAO: ").append(dataEmissao).append("\r\n");
        sb.append("T 0 2 60 177 HORA EMISSAO: ").append(horaEmissao).append("\r\n");
        sb.append("T 5 0 3 181 ").append(nomeCompromissario).append("\r\n");
        sb.append("T 7 0 3 184 ").append((CharSequence) sbEndereco).append("\r\n");
        sb.append("T 7 0 3 187 ").append(complemento).append("\r\n");
        sb.append("T 7 0 3 190 Rota: ").append(rota).append("\r\n");
        sb.append("T 7 0 15 194 COD. LIGACAO").append("\r\n");
        StringBuilder append4 = sb.append("T 7 0 18 197 ");
        String complemento2 = leiturasVO.getInstalacaoCag();
        append4.append(complemento2).append("\r\n");
        sb.append("T 7 0 18 201 VALIDADE").append("\r\n");
        sb.append("T 7 0 17 204 ").append(Utils.format(fatsimultaneoVO.getLixoVenctoFsi())).append("\r\n");
        sb.append("T 7 0 60 201 VALOR A PAGAR").append("\r\n");
        sb.append("T 7 0 65 204 R$ ").append(df.format(fatsimultaneoVO.getLixoValorFsi())).append("\r\n");
        sb.append("CENTER\r\n");
        sb.append("T 5 0 0 210 ").append(BoletoUtils.isGuiaArrecadacao(fatsimultaneoVO.getLixoBarrasFsi()).booleanValue() ? BoletoUtils.getLinhaDigitavelArrecadacao(fatsimultaneoVO.getLixoBarrasFsi()) : BoletoUtils.getLinhaDigitavel(fatsimultaneoVO.getLixoBarrasFsi())).append("\r\n");
        sb.append("B I2OF5 0.245 25 8 0 213 ").append(fatsimultaneoVO.getLixoBarrasFsi()).append("\r\n");
        sb.append("FORM\r\n");
        sb.append("PRINT\r\n");
        return sb.toString();
    }

    public Map<String, String> formatarLancamento(AgFatsimultaneolancaVO lancamento) {
        Map<String, String> map = new HashMap<>();
        try {
            String valor = this.df.format(lancamento.getValorFsl());
            map.put("descricao", "Recuperacao(Multa e Juros)");
            map.put("valor", valor);
            return map;
        } catch (Exception e) {
            map.put("descricao", lancamento.getDescricaoFsl());
            map.put("valor", this.df.format(lancamento.getValorFsl()));
            return map;
        }
    }

    public boolean lancamentoDeResiduo(AgFatsimultaneolancaVO lancamento) {
        return lancamento != null && Objects.equals(lancamento.getTipoFsl(), "I");
    }

    public String formatarValorCredito(Double valor) {
        String valorFormatado = this.df.format(Utils.roundDouble(BigDecimal.valueOf(valor.doubleValue())));
        return LanguageTag.SEP + valorFormatado + "\r\n";
    }

    /* JADX WARN: Removed duplicated region for block: B:54:0x037d  */
    /* JADX WARN: Removed duplicated region for block: B:55:0x0386  */
    @Override // br.com.fiorilli.leitura.print.cpcl.Cpcl
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct add '--show-bad-code' argument
    */
    public java.lang.String getNotificacaoDebito(br.com.fiorilli.leitura.vo.agua.AgLeiturasAndroidVO r42, java.util.List<br.com.fiorilli.leitura.vo.notificacoes.NotificacaoAguaVO> r43, br.com.fiorilli.leitura.vo.financeiro.LancamentoAndroidVO r44, br.com.fiorilli.leitura.vo.agua.AgFaturamentosimultaneoVO r45, java.lang.String r46, java.lang.String r47) throws java.lang.Exception {
        /*
            Method dump skipped, instructions count: 1255
            To view this dump add '--comments-level debug' option
        */
        throw new UnsupportedOperationException("Method not decompiled: br.com.fiorilli.leitura.print.cpcl.ZQ521.CpclAraputangaZQ521.getNotificacaoDebito(br.com.fiorilli.leitura.vo.agua.AgLeiturasAndroidVO, java.util.List, br.com.fiorilli.leitura.vo.financeiro.LancamentoAndroidVO, br.com.fiorilli.leitura.vo.agua.AgFaturamentosimultaneoVO, java.lang.String, java.lang.String):java.lang.String");
    }

    @Override // br.com.fiorilli.leitura.print.cpcl.Cpcl
    protected String getAnaliseAgua() throws ParseException {
        StringBuilder sb = new StringBuilder();
        AgQualidadeVO qualidadeVO = getAgQualidadeVO();
        if (!Utils.isNull(qualidadeVO)) {
            sb.append("T 7 0 8 158 Cloro ").append("\r\n");
            sb.append("T 7 0 28 158 ").append(!Utils.isNullOrEmpty(qualidadeVO.getUcloroAql()) ? qualidadeVO.getUcloroAql() : " - ").append("\r\n");
            sb.append("T 7 0 40 158 ").append(!Utils.isNullOrEmpty(qualidadeVO.getPcloroAql()) ? qualidadeVO.getPcloroAql() : " - ").append("\r\n");
            sb.append("T 7 0 65 158 ").append("1").append("\r\n");
            sb.append("T 7 0 85 158 ").append(!Utils.isNullOrEmpty(qualidadeVO.getRcloroAql()) ? qualidadeVO.getRcloroAql() : " - ").append("\r\n");
            sb.append("T 7 0 8 161 Ph ").append("\r\n");
            sb.append("T 7 0 28 161 ").append(!Utils.isNullOrEmpty(qualidadeVO.getUphAql()) ? qualidadeVO.getUphAql() : " - ").append("\r\n");
            sb.append("T 7 0 40 161 ").append(!Utils.isNullOrEmpty(qualidadeVO.getPphAql()) ? qualidadeVO.getPphAql() : " - ").append("\r\n");
            sb.append("T 7 0 65 161 ").append("1").append("\r\n");
            sb.append("T 7 0 85 161 ").append(!Utils.isNullOrEmpty(qualidadeVO.getRphAql()) ? qualidadeVO.getRphAql() : " - ").append("\r\n");
            sb.append("T 7 0 8 164 Fluoreto ").append("\r\n");
            sb.append("T 7 0 28 164 ").append(!Utils.isNullOrEmpty(qualidadeVO.getUfluorAql()) ? qualidadeVO.getUfluorAql() : " - ").append("\r\n");
            sb.append("T 7 0 40 164 ").append(!Utils.isNullOrEmpty(qualidadeVO.getPfluorAql()) ? qualidadeVO.getPfluorAql() : " - ").append("\r\n");
            sb.append("T 7 0 65 164 ").append("1").append("\r\n");
            sb.append("T 7 0 85 164 ").append(!Utils.isNullOrEmpty(qualidadeVO.getRfluorAql()) ? qualidadeVO.getRfluorAql() : " - ").append("\r\n");
            sb.append("T 7 0 8 167 Cor").append("\r\n");
            sb.append("T 7 0 28 167 ").append(!Utils.isNullOrEmpty(qualidadeVO.getUcorAql()) ? qualidadeVO.getUcorAql() : " - ").append("\r\n");
            sb.append("T 7 0 40 167 ").append(!Utils.isNullOrEmpty(qualidadeVO.getPcorAql()) ? Utils.removeAcentos(qualidadeVO.getPcorAql()) : " - ").append("\r\n");
            sb.append("T 7 0 65 167 ").append("1").append("\r\n");
            sb.append("T 7 0 85 167 ").append(!Utils.isNullOrEmpty(qualidadeVO.getRcorAql()) ? qualidadeVO.getRcorAql() : " - ").append("\r\n");
            sb.append("T 7 0 8 170 Turbidez").append("\r\n");
            sb.append("T 7 0 28 170 ").append(!Utils.isNullOrEmpty(qualidadeVO.getUturbiAql()) ? qualidadeVO.getUturbiAql() : " - ").append("\r\n");
            sb.append("T 7 0 40 170 ").append(!Utils.isNullOrEmpty(qualidadeVO.getPturbiAql()) ? Utils.removeAcentos(qualidadeVO.getPturbiAql()) : " - ").append("\r\n");
            sb.append("T 7 0 65 170 ").append("1").append("\r\n");
            sb.append("T 7 0 85 170 ").append(!Utils.isNullOrEmpty(qualidadeVO.getRturbiAql()) ? qualidadeVO.getRturbiAql() : " - ").append("\r\n");
            sb.append("T 7 0 6 173 Colif. fecais ").append("\r\n");
            sb.append("T 7 0 28 173 ").append(!Utils.isNullOrEmpty(qualidadeVO.getUcolifAql()) ? qualidadeVO.getUcolifAql() : " - ").append("\r\n");
            sb.append("T 7 0 40 173 ").append(!Utils.isNullOrEmpty(qualidadeVO.getPcolifAql()) ? qualidadeVO.getPcolifAql() : " - ").append("\r\n");
            sb.append("T 7 0 65 173 ").append("1").append("\r\n");
            sb.append("T 7 0 85 173 ").append(!Utils.isNullOrEmpty(qualidadeVO.getRcolifAql()) ? qualidadeVO.getRcolifAql() : " - ").append("\r\n");
            sb.append("T 7 0 6 176 Colif. totais ").append("\r\n");
            sb.append("T 7 0 28 176 ").append(!Utils.isNullOrEmpty(qualidadeVO.getUcolitAql()) ? qualidadeVO.getUcolitAql() : " - ").append("\r\n");
            sb.append("T 7 0 40 176 ").append(!Utils.isNullOrEmpty(qualidadeVO.getPcolitAql()) ? qualidadeVO.getPcolitAql() : " - ").append("\r\n");
            sb.append("T 7 0 65 176 ").append("1").append("\r\n");
            sb.append("T 7 0 85 176 ").append(Utils.isNullOrEmpty(qualidadeVO.getRcolitAql()) ? " - " : qualidadeVO.getRcolitAql()).append("\r\n");
        }
        return sb.toString();
    }
}
