function FindProxyForURL(url, host) {
    var i;
    var direct = "DIRECT";
    var generalPurposeProxy = "PROXY proxy.creditagricole:8080; PROXY proxy2.creditagricole:8080";
    var applicationProxy = "PROXY pxapp.creditagricole:8080; PROXY pxapp2.creditagricole:8080";
    var drcProxyFirst = "PROXY proxy2.creditagricole:8080; PROXY proxy.creditagricole:8080";

    // hosty lokalne, do których łączymy się przez proxy ogólnego przeznaczenia
    var localHostsViaGeneralPurposeProxy = [
        "emarketing.efl.com.pl",
        "wielkiodkrywca.efl.com.pl"
    ];

    // domeny lokalne
    var localDomains = [
        ".creditagricole",
        ".grupa.lukas",
        ".lukas",
        ".efl.com.pl",
        ".eflservice.pl",
        ".catest",
        ".ca-test.pl",
        ".ca-ubezpieczenia",
        ".local"
    ];

    // hosty lokalne nie objęte przez localDomains, do których łączymy się bezpośrednio
    var localHostsDirect = [
        "adfs.credit-agricole.pl",
        "partnerweb.credit-agricole.pl",
        "quark.credit-agricole.pl",
        "attachments.quark.credit-agricole.pl",
        "autodiscover.credit-agricole.pl",
        "pki.credit-agricole.pl",
        "pki1.credit-agricole.pl",
        "pki2.credit-agricole.pl",
        "ocsp.credit-agricole.pl",
        "mdm.credit-agricole.pl",
        "tmms.credit-agricole.pl",
        "ca24.credit-agricole.pl",
        "apiportal.credit-agricole.pl",
        "www.tideplatform.com",
        "tideplatform.com",
        "raporter-cali.scc24.pl",
        "3cx-ca.scc24.pl",
        "swd.zbp.pl",
        "strefabiznesu.credit-agricole.pl",
        "archiwum.credit-agricole.pl",
        "login-client-archiwum.credit-agricole.pl",
        "caubezpieczenia.scc24.pl",
        "caubezpieczeniaapi.scc24.pl",
        "caubezpieczeniaid.scc24.pl",
        "nextpbx-01.scc24.pl",
        "nextpbx-02.scc24.pl",
        "mobilca-p24.credit-agricole.pl",
        "uas-c.ca-collaboration.com",
        "uas-oc.ca-collaboration.com",
        "uas-pp.ca-collaboration.com"
    ];

    // aplikacje biznesowe, do których łączymy się przez proxy aplikacyjne
    var businessApplications = [
        "thomsonreuters.com",
        "*.thomsonreuters.com",
        "thomsonreuters.net",
        "*.thomsonreuters.net",
        "refinitiv.com",
        "*.refinitiv.com",
        "refinitiv.net",
        "*.refinitiv.net",
        "refinitiv.biz",
        "*.refinitiv.biz",
        "*.emea.cib",
        "*.asia.cib",
        "*.group.gca",
        "*.credit-agricole.fr",
        "redifx.uk.gs.com",
        "*.jpmorgan.com",
        "credit-agricole.pl",
        "*.credit-agricole.pl",
        "caraty.pl",
        "www.caraty.pl",
        "klubrabatowy.pl",
        "www.klubrabatowy.pl",
        "oney24.pl",
        "www.oney24.pl",
        "prm360.pl",
        "www.prm360.pl",
        "aukcje.efl.com.pl",
        "impel.vcms24.pl",
        "www.obiegfaktur.ist.pl",
        "ca.pika.pl",
        "sws.topcard.pl",
        "*.blue.pl",
        "*.swd.zbp.pl",
        "*.blue.pl",
        "*.uat.ognivo.pl",
        "*.bloomberg.net",
        "*.zus.pl",
        "tpeweb.paybox.com"
    ];

    // strony, do których łączymy się przez proxy w DRC
    var viaDrcProxy = [
        "canalchat.fr",
        "*.canalchat.fr",
        "caremotshow.lives.studio",
        "*.vimeo.com",
        "*.vimeocdn.com",
        "133vod-adaptive.akamaized.net",
        "177vod-adaptive.akamaized.net"
    ];

    // domeny Azure, których używają usługi mogące wykorzystywać private links
    var azurePrivateLinksPossible = [
        "adf.azure.com",
        "agentsvc.azure-automation.net",
        "api.azureml.ms",
        "azure-automation.net",
        "azurecr.io",
        "azuredatabricks.net",
        "blob.core.windows.net",
        "database.windows.net",
        "datafactory.azure.net",
        "dfs.core.windows.net",
        "documents.azure.com",
        "eventgrid.azure.net",
        "inference.ml.azure.com",
        "managedhsm.azure.net",
        "monitor.azure.com",
        "mongo.cosmos.azure.com",
        "notebooks.azure.net",
        "ods.opinsights.azure.com",
        "oms.opinsights.azure.com",
        "openai.azure.com",
        "postgres.database.azure.com",
        "queue.core.windows.net",
        "redis.cache.windows.net",
        "servicebus.windows.net",
        "vault.azure.net",
        "vaultcore.azure.net",
        "we.backup.windowsazure.com",
        "westeurope.azmk8s.io"
    ];

    // domeny AWS, których używają usługi mogące wykorzystywać private links
    var awsPrivateLinksPossible = [
        "amazonaws.com",
        "privatelink.snowflakecomputing.com"
    ];

    host = host.toLowerCase();

    // połączenia do hostów lokalnych przez proxy ogólnego przeznaczenia
    for (i = 0; i < localHostsViaGeneralPurposeProxy.length; i++) {
        if (shExpMatch(host, localHostsViaGeneralPurposeProxy[i])) {
            return generalPurposeProxy;
        }
    }

    // połączenia bezpośrednie do hostów z domen lokalnych
    for (i = 0; i < localDomains.length; i++) {
        if (dnsDomainIs(host, localDomains[i])) {
            return direct;
        }
    }

    // połączenia bezpośrednie do hostów lokalnych spoza localDomains
    for (i = 0; i < localHostsDirect.length; i++) {
        if (shExpMatch(host, localHostsDirect[i])) {
            return direct;
        }
    }

    // połączenia do aplikacji biznesowych przez proxy aplikacyjne
    for (i = 0; i < businessApplications.length; i++) {
        if (shExpMatch(host, businessApplications[i])) {
            return applicationProxy;
        }
    }

    // połączenia przez proxy w DRC
    for (i = 0; i < viaDrcProxy.length; i++) {
        if (shExpMatch(host, viaDrcProxy[i])) {
            return drcProxyFirst;
        }
    }

    // połączenia do usług Azure mogących wykorzystywać private links
    for (i = 0; i < azurePrivateLinksPossible.length; i++) {
        if (dnsDomainIs(host, azurePrivateLinksPossible[i])) {
            var ipAddress = dnsResolve(host);
            if (isInNet(ipAddress, '10.200.0.0', '255.255.0.0')) {
                return direct;
            }
            return generalPurposeProxy;
        }
    }

    // połączenie bezpośrednie do localhost
    if (host === '127.0.0.1' || host === '::1' || 
        host === 'localhost' || host === 'localhost.localdomain') {
        return direct;
    }

    // połączenia bezpośrednie do prywatnych adresów IP
    if (/^\d+\.\d+\.\d+\.\d+$/.test(host) &&
        (isInNet(host, '172.16.0.0', '255.240.0.0') ||
         isInNet(host, '192.168.0.0', '255.255.0.0') ||
         isInNet(host, '10.0.0.0', '255.0.0.0'))) {
        return direct;
    }

    // połączenie bezpośrednie, gdy użyto krótkiej nazwy
    if (isPlainHostName(host)) {
        return direct;
    }

    return generalPurposeProxy;
}
