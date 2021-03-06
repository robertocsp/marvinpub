function get_endereco(psid)
{
    var url = '/marviin/api/rest/endereco_cliente';
    if (psid)
        url += '?psid='+psid
    else
        url += '/' + $('input#path').val();
    $.getJSON( url, function( data ) {
        if(data && data.length)
        {
            $('#lista-enderecos').html('');
            data.forEach(function (item, index){
                var label = $('<label></label>').attr('class', 'endereco');
                var input = $('<input></input>')
                    .attr('type', 'radio')
                    .attr('name', 'endereco_entrega')
                    .attr('value', item.id);
                if(item.padrao == true)
                    input.prop('checked', true);
                var endereco = ' ' + item.endereco + ' ' + item.complemento + ', ' + item.bairro + ', CEP: ' + item.cep + ', ' + item.cidade + ', ' + item.estado;
                label.append(input).append($('<span></span>').append(endereco));
                $('#lista-enderecos').append(label);
            });
            $('form#form-endereco').validate({
                rules: {
                    endereco_entrega: { required: true },
                },
                submitHandler: function(form) {
                    if(psid)
                        form.action += '&psid=' + psid;
                    form.submit();
                },
                onfocusout: false,
                onkeyup: false,
                onclick: false
            });
            $('button#btn-escolher-endereco').removeClass('none');
        }
        else
            $('#lista-enderecos').html('Nenhum endereço encontrado. Utilize o botão abaixo para cadastrar seu endereço de entrega. Obrigado.');
        $('a#btn-adicionar-endereco').removeClass('none');
    })
    .fail(function(error) {
        if(error.message)
            $('#lista-enderecos').html(error.message);
        else
            $('#lista-enderecos').html('Desculpe, mas não foi possível recuperar seus endereços, por favor, refaça o login e tente novamente.');
    })
    .always(function() {
        $('div.loading-marviin').removeClass('block');
    });
}

function process_action(psid)
{
    if(!!$('div.close-window')[0])
    {
        var url = '/marviin/api/rest/endereco_cliente';
        if (psid)
            url += '?psid='+psid
        else
            url += '/' + $('input#path').val();
        $.post(url, function(data) {
            console.log(data);
            if(psid)
            {
                MessengerExtensions.requestCloseBrowser(function success() {
                    //nada a fazer
                }, function error(err) {
                    //TODO informar o usuário que ele pode fechar a WEBVIEW.
                });
            }
            else
            {
                window.location.href='https://www.messenger.com/closeWindow/?image_url=-&display_text=-';
            }
        })
        .fail(function(data) {
            if(error.message)
                $('#lista-enderecos').html(error.message);
            else
                $('#lista-enderecos').html('Desculpe, tivemos um erro inesperado, por favor, tente novamente.')
        })
        .always(function() {
            $('div.loading-marviin').removeClass('block');
        });
        return;
    }
    $('button#btn-escolher-endereco').on('click', function (e){
        if($(this).hasClass('nosubmit') && !!$('[type=radio]:checked')[0])
        {
            $(this).removeClass('nosubmit');
        }
        if($(this).hasClass('nosubmit'))
        {
            e.preventDefault();
            return false;
        }
        $(this).addClass('nosubmit');
    });
    $.extend(
        $.validator.messages, {
            required: 'Campo obrigatório.',
        }
    );
    get_endereco(psid);
}

function error_handler(err)
{
    $('#lista-enderecos').html('Desculpe, mas não consegui recuperar seus endereços, por favor, refaça o login e tente novamente.');
}